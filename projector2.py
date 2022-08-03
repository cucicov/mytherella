# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

"""Project given image to the latent space of pretrained network pickle."""

import copy
import os
from time import perf_counter

import click
import numpy as np
import PIL.Image
import torch
import torch.nn.functional as F

import dnnlib
import legacy

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

target_features = None


class SeedPhotoEventHandler(FileSystemEventHandler):

    def on_any_event(self, event):
        if (not event.is_directory) and (event.event_type == 'closed'):
            print('modified: ' + event.src_path)
            target_pil = PIL.Image.open(event.src_path).convert('RGB')
            w, h = target_pil.size
            s = min(w, h)
            target_pil = target_pil.crop(((w - s) // 2, (h - s) // 2, (w + s) // 2, (h + s) // 2))
            target_pil = target_pil.resize((G.img_resolution, G.img_resolution), PIL.Image.LANCZOS)
            target_uint8 = np.array(target_pil, dtype=np.uint8)

            local_target = torch.tensor(target_uint8.transpose([2, 0, 1]), device=device)

            target_images = local_target.unsqueeze(0).to(device).to(torch.float32)
            if target_images.shape[2] > 256:
                target_images = F.interpolate(target_images, size=(256, 256), mode='area')
            global target_features
            target_features = vgg16(target_images, resize_images=False, return_lpips=True)

            global stepCounter
            stepCounter = 0

            global start_time
            start_time = perf_counter()


def project(
        G,
        target: torch.Tensor,  # [C,H,W] and dynamic range [0,255], W & H must match G output resolution
        *,
        w_avg_samples=10000,
        initial_learning_rate=0.1,
        initial_noise_factor=0.05,
        lr_rampdown_length=0.25,
        lr_rampup_length=0.05,
        noise_ramp_length=0.75,
        regularize_noise_weight=1e5,
        constant_learning_rate=False,
        verbose=False,
        device: torch.device
):
    assert target.shape == (G.img_channels, G.img_resolution, G.img_resolution)

    def logprint(*args):
        if verbose:
            print(*args)

    G = copy.deepcopy(G).eval().requires_grad_(False).to(device)  # type: ignore

    # Compute w stats.
    logprint(f'Computing W midpoint and stddev using {w_avg_samples} samples...')
    z_samples = np.random.RandomState(123).randn(w_avg_samples, G.z_dim)
    w_samples = G.mapping(torch.from_numpy(z_samples).to(device), None)  # [N, L, C]
    w_samples = w_samples[:, :1, :].cpu().numpy().astype(np.float32)  # [N, 1, C]
    w_avg = np.mean(w_samples, axis=0, keepdims=True)  # [1, 1, C]
    w_std = (np.sum((w_samples - w_avg) ** 2) / w_avg_samples) ** 0.5

    # Setup noise inputs.
    noise_bufs = {name: buf for (name, buf) in G.synthesis.named_buffers() if 'noise_const' in name}

    # Load VGG16 feature detector.
    url = 'https://nvlabs-fi-cdn.nvidia.com/stylegan2-ada-pytorch/pretrained/metrics/vgg16.pt'
    with dnnlib.util.open_url(url) as f:
        global vgg16
        vgg16 = torch.jit.load(f).eval().to(device)

    # Features for target image.
    target_images = target.unsqueeze(0).to(device).to(torch.float32)
    if target_images.shape[2] > 256:
        target_images = F.interpolate(target_images, size=(256, 256), mode='area')
    global target_features
    target_features = vgg16(target_images, resize_images=False, return_lpips=True)

    w_opt = torch.tensor(w_avg, dtype=torch.float32, device=device, requires_grad=True)  # pylint: disable=not-callable
    # w_out = torch.zeros([num_steps] + list(w_opt.shape[1:]), dtype=torch.float32, device=device)
    optimizer = torch.optim.Adam([w_opt] + list(noise_bufs.values()), betas=(0.9, 0.999), lr=initial_learning_rate)

    # Init noise.
    for buf in noise_bufs.values():
        buf[:] = torch.randn_like(buf)
        buf.requires_grad = True

    # for step in range(num_steps):
    global stepCounter
    stepCounter = 0

    while 1:
        stepCounter = stepCounter + 0.1
        # Learning rate schedule.

        t = 1 / stepCounter
        w_noise_scale = w_std * initial_noise_factor * max(0.0, 1.0 - t / noise_ramp_length) ** 2
        if constant_learning_rate:
            # Turn off the rampup/rampdown of the learning rate
            lr_ramp = 1.0
            print('---- constant learning rate ----')
        else:
            lr_ramp = min(1.0, (1.0 - t) / lr_rampdown_length)
            lr_ramp = 0.5 - 0.5 * np.cos(lr_ramp * np.pi)
            lr_ramp = lr_ramp * min(1.0, t / lr_rampup_length)
        lr = initial_learning_rate * lr_ramp
        for param_group in optimizer.param_groups:
            param_group['lr'] = lr

        print("Learning rate: " + str(lr))

        # Synth images from opt_w.
        w_noise = torch.randn_like(w_opt) * w_noise_scale
        ws = (w_opt + w_noise).repeat([1, G.mapping.num_ws, 1])
        synth_images = G.synthesis(ws, noise_mode='const')

        # Downsample image to 256x256 if it's larger than that. VGG was built for 224x224 images.
        synth_images = (synth_images + 1) * (255 / 2)
        if synth_images.shape[2] > 256:
            synth_images = F.interpolate(synth_images, size=(256, 256), mode='area')

        # Features for synth images.
        synth_features = vgg16(synth_images, resize_images=False, return_lpips=True)
        dist = (target_features - synth_features).square().sum()

        # Noise regularization.
        reg_loss = 0.0
        for v in noise_bufs.values():
            noise = v[None, None, :, :]  # must be [1,1,H,W] for F.avg_pool2d()
            while True:
                reg_loss += (noise * torch.roll(noise, shifts=1, dims=3)).mean() ** 2
                reg_loss += (noise * torch.roll(noise, shifts=1, dims=2)).mean() ** 2
                if noise.shape[2] <= 8:
                    break
                noise = F.avg_pool2d(noise, kernel_size=2)
        loss = dist + reg_loss * regularize_noise_weight

        # Step
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        optimizer.step()
        # logprint(f'step {step + 1:>4d}/{num_steps}: dist {dist:<4.2f} loss {float(loss):<5.2f}')

        projected_w = w_opt.detach()[0].unsqueeze(0).repeat([1, G.mapping.num_ws, 1])
        # synth_image = G.synthesis(projected_w.unsqueeze(0), noise_mode='const')  # remove unsqueeze?
        synth_image = G.synthesis(projected_w, noise_mode='const')
        synth_image = (synth_image + 1) * (255 / 2)
        synth_image = synth_image.permute(0, 2, 3, 1).clamp(0, 255).to(torch.uint8)[0].cpu().numpy()
        PIL.Image.fromarray(synth_image, 'RGB').save(f'projector/1.jpg')  # TODO: add variable?

        # Save projected W for each optimization step.
        # w_out[step] = w_opt.detach()[0]

        # Normalize noise.
        with torch.no_grad():
            for buf in noise_bufs.values():
                buf -= buf.mean()
                buf *= buf.square().mean().rsqrt()

        timePassed = (perf_counter() - start_time)
        if ((int(perf_counter() % 300) == 0) or (timePassed > 15 and lr < 0.02)):
            print("BREAK+++++++\n")
            break
        print("timePassed:" + str(perf_counter() % 600) + "\n")


# ----------------------------------------------------------------------------

@click.command()
@click.option('--network', 'network_pkl', help='Network pickle filename', required=True)
@click.option('--target', 'target_fname', help='Target image file to project to', required=True, metavar='FILE')
@click.option('--listenerFolder', 'listener_folder', help='folder to save new images into for the display listener',
              required=True, metavar='FILE')
@click.option('--outdir', help='Where to save the output images', required=True, metavar='DIR')
@click.option('--constant-lr', 'constant_learning_rate', is_flag=True,
              help='Add flag to use a constant learning rate throughout the optimization (turn off the rampup/rampdown)')
def run_projection(
        network_pkl: str,
        target_fname: str,
        outdir: str,
        constant_learning_rate: bool,
        listener_folder: str
):
    while 1:
        """Project given image to the latent space of pretrained network pickle.
    
        Examples:
    
        \b
        python projector.py --outdir=out --target=~/mytargetimg.png \\
            --network=https://nvlabs-fi-cdn.nvidia.com/stylegan2-ada-pytorch/pretrained/ffhq.pkl
        """
        # np.random.seed(seed)
        # torch.manual_seed(seed)

        # define observer for seed change
        event_handler = SeedPhotoEventHandler()
        observer = Observer()
        observer.schedule(event_handler, listener_folder, recursive=True)
        observer.start()

        # Load networks.
        print('Loading networks from "%s"...' % network_pkl)
        global device
        device = torch.device('cuda')
        with dnnlib.util.open_url(network_pkl) as fp:
            global G
            G = legacy.load_network_pkl(fp)['G_ema'].requires_grad_(False).to(device)  # type: ignore

        # Load target image.
        target_pil = PIL.Image.open(target_fname).convert('RGB')
        w, h = target_pil.size
        s = min(w, h)
        target_pil = target_pil.crop(((w - s) // 2, (h - s) // 2, (w + s) // 2, (h + s) // 2))
        target_pil = target_pil.resize((G.img_resolution, G.img_resolution), PIL.Image.LANCZOS)
        target_uint8 = np.array(target_pil, dtype=np.uint8)

        # Optimize projection.
        global start_time
        start_time = perf_counter()
        projected_w_steps = project(
            G,
            target=torch.tensor(target_uint8.transpose([2, 0, 1]), device=device),  # pylint: disable=not-callable
            device=device,
            verbose=True,
            constant_learning_rate=constant_learning_rate
        )
        print(f'Elapsed: {(perf_counter() - start_time):.1f} s')

        # Render debug output: optional video and projected image and W vector.
        os.makedirs(outdir, exist_ok=True)

        # Save final projected frame and W vector.
        # target_pil.save(f'{outdir}/target.png')
        # projected_w = projected_w_steps[-1]
        # synth_image = G.synthesis(projected_w.unsqueeze(0), noise_mode='const')
        # synth_image = (synth_image + 1) * (255 / 2)
        # synth_image = synth_image.permute(0, 2, 3, 1).clamp(0, 255).to(torch.uint8)[0].cpu().numpy()
        # PIL.Image.fromarray(synth_image, 'RGB').save(f'{outdir}/proj.png')
        # np.savez(f'{outdir}/projected_w.npz', w=projected_w.unsqueeze(0).cpu().numpy())

        # moved the video to the end so we can look at images while these videos take time to compile
        # if save_video:
        #     video = imageio.get_writer(f'{outdir}/proj.mp4', mode='I', fps=10, codec='libx264', bitrate='16M')
        #     print (f'Saving optimization progress video "{outdir}/proj.mp4"')
        #     for projected_w in projected_w_steps:
        #         synth_image = G.synthesis(projected_w.unsqueeze(0), noise_mode='const')
        #         synth_image = (synth_image + 1) * (255/2)
        #         synth_image = synth_image.permute(0, 2, 3, 1).clamp(0, 255).to(torch.uint8)[0].cpu().numpy()
        #         video.append_data(np.concatenate([target_uint8, synth_image], axis=1))
        #     video.close()


# ----------------------------------------------------------------------------

if __name__ == "__main__":
    run_projection()  # pylint: disable=no-value-for-parameter

# ----------------------------------------------------------------------------
