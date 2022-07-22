import processing.serial.*;
import ddf.minim.*;

Serial myPort;  // Create object from Serial class
String val;     // Data received from the serial port

PImage bg;

Minim minim;
AudioPlayer noise;
AudioPlayer fox;
AudioPlayer wave;

AudioPlayer[] sound_mapping = new AudioPlayer[10];

static int IMAGE_FOUND_INI = 10;
int image_found_counter = IMAGE_FOUND_INI;

boolean displayImage = false;
int imageId = 0;
int[][] img_coord = {
  {427, 580},
  {1229, 178},
  {714, 668},
  {662, 749},
  {612, 764},
  {609, 329},
  {326, 629},
  {572, 351},
  {545, 555},
  {688, 670}
};

PImage img0, img1, img2, img3, img4, img5, img6, img7, img8, img9;

PImage seed_images[] = new PImage[10];

int img_size = 128;

int posY = -1;
int posX = -1;

int last_image_id = -1;

boolean gainShifting = false;

void setup() {
  //size(1920, 1080);
  fullScreen();
  background(255);
  // I know that the first port in the serial list on my mac
  // is Serial.list()[0].
  // On Windows machines, this generally opens COM1.
  // Open whatever port is the one you're using.
  //println(Serial.list());
  String portName = Serial.list()[0]; //change the 0 to a 1 or 2 etc. to match your port
  myPort = new Serial(this, portName, 9600);

  bg = loadImage("bg.png");
  
  strokeWeight(2);
  stroke(0, 255, 0);
  
  img0 = loadImage("/home/c/Documents/mytherella/seed_img/0.png");
  img1 = loadImage("/home/c/Documents/mytherella/seed_img/1.png");
  img2 = loadImage("/home/c/Documents/mytherella/seed_img/2.png");
  img3 = loadImage("/home/c/Documents/mytherella/seed_img/3.png");
  img4 = loadImage("/home/c/Documents/mytherella/seed_img/4.png");
  img5 = loadImage("/home/c/Documents/mytherella/seed_img/5.png");
  img6 = loadImage("/home/c/Documents/mytherella/seed_img/6.png");
  img7 = loadImage("/home/c/Documents/mytherella/seed_img/7.png");
  img8 = loadImage("/home/c/Documents/mytherella/seed_img/8.png");
  img9 = loadImage("/home/c/Documents/mytherella/seed_img/9.png");
  seed_images[0] = img0;
  seed_images[1] = img1; //<>//
  seed_images[2] = img2;
  seed_images[3] = img3;
  seed_images[4] = img4;
  seed_images[5] = img5;
  seed_images[6] = img6;
  seed_images[7] = img7;
  seed_images[8] = img8;
  seed_images[9] = img9;
  
  minim = new Minim(this);
  noise = minim.loadFile("noise.mp3", 2048);
  fox = minim.loadFile("chimes.wav", 2048);
  wave = minim.loadFile("wave.wav", 2048);
  fox.loop();
  wave.loop();
  noise.loop();
  noise.setGain(10);
  
  fox.setGain(-50);
  wave.setGain(-50);
  
  sound_mapping[0] = wave;
  sound_mapping[1] = wave;
  sound_mapping[2] = wave;
  sound_mapping[3] = wave;
  sound_mapping[4] = wave;
  sound_mapping[5] = fox;
  sound_mapping[6] = wave;
  sound_mapping[7] = wave;
  sound_mapping[8] = wave;
  sound_mapping[9] = wave;
} //<>//

void draw() {
  background(bg);
  
  if ( myPort.available() > 0) {  // If data is available,
    val = myPort.readStringUntil('\n');         // read it and store it in val
  }

  color(0);
  if (val != null && val.strip().split("-").length == 2) {
    int x = int(val.strip().split("-")[0]);
    int y = int(val.strip().split("-")[1]);
    posY = int(map(x, 0, 1023, 0, height));
    posX = int(map(y, 0, 1023, width, 0));
    line(0, posY, width, posY); //<>//
    line(posX, 0, posX, height);
    
  }
  
  
  
  // process sound map -----
  
  fox.setGain(-50);
 
  Integer[] ids;
  int area_for_sound_2 = 50;
  ids = checkImageFound(posX, posY, area_for_sound_2);
  setGlobalGains(ids, -20);
  
  int area_for_sound_1 = 30;
  ids = checkImageFound(posX, posY, area_for_sound_1);
  setGlobalGains(ids, -10);
  
  int area_for_sound_0 = 10;
  ids = checkImageFound(posX, posY, area_for_sound_0);
  setGlobalGains(ids, 10);
  
  // process image finding -------
  
  int area_for_image_found = 10;
  Integer[] image_ids = checkImageFound(posX, posY, area_for_image_found); 
  
  if (image_ids.length > 0) {
    image_found_counter = IMAGE_FOUND_INI;
    last_image_id = image_ids[0]; // only one image can be found actually.
    image(seed_images[last_image_id], img_coord[last_image_id][0], img_coord[last_image_id][1], img_size, img_size);
  } else {
    image_found_counter--;
  }
  
  if (image_found_counter > -1 && last_image_id > -1) {
    img_size += 50;
    if (img_size > 412) {
      img_size = 412;
    }
    image(seed_images[last_image_id], img_coord[last_image_id][0], img_coord[last_image_id][1], img_size, img_size);
    
    if (noise.getGain() > -50 && !gainShifting) {
      noise.shiftGain(noise.getGain(), -50, 3000);
      gainShifting = true;
    } else {
      gainShifting = false;
    }
  } else {
    img_size = 128;
    
    if (noise.getGain() < 10) {
      noise.shiftGain(noise.getGain(), 10, 3000);
      gainShifting = true;
    } else {
      gainShifting = false;
    }
  }
  
  // ----------
  
}

void setGlobalGains(Integer[] ids, int gain) {
  if (ids.length > 0) {
    for (int i = 0; i < ids.length; i++) {
      int foundId = ids[i];
      sound_mapping[foundId].setGain(gain);
    }
  }
}

Integer[] checkImageFound(int posX, int posY, int area) {
  ArrayList<Integer> found_img_ids = new ArrayList<Integer>();
  for (int i=0; i<img_coord.length; i++) {
    if (abs(img_coord[i][0] - posX) <= area && abs(img_coord[i][1] - posY) <= area) {
      println("found:" + i);
      found_img_ids.add(i);
    }
  }
  return found_img_ids.toArray(new Integer[found_img_ids.size()]);
}

void mouseClicked() {
  displayImage = !displayImage;
  imageId = 0;
  img_size = 128;
  println(mouseX, mouseY);
  
}
