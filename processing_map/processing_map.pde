import processing.serial.*;
import ddf.minim.*;
import java.nio.file.*;


String sourceSeed = "/home/c/Documents/mytherella/seed_img/";
String sourceNormal = "/home/c/Documents/mytherella/normal_img/";
String dest = "/home/c/Documents/mytherella/projector/seed/";

Serial myPort;  // Create object from Serial class
String val;     // Data received from the serial port

PImage bg;

Minim minim;
AudioPlayer noise;
AudioPlayer fox;
AudioPlayer wave;
AudioPlayer d1;
AudioPlayer d2;
AudioPlayer d3;
AudioPlayer d4;
AudioPlayer d5;
AudioPlayer d6;
AudioPlayer d7;
AudioPlayer d8;

AudioPlayer[] sound_mapping = new AudioPlayer[10];

static int IMAGE_FOUND_INI = 10; // this defines the area for finding the image, the smaller the area the harder the game.
int image_found_counter = IMAGE_FOUND_INI;
int area_for_image_found = IMAGE_FOUND_INI;

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

// vars for seed images
int normalImageId = 0;
static int NORMAL_IMAGES_GAP = 20;
boolean insertNormalImage = true;
boolean seedImageFound = false;


void setup() {
  size(1920, 1080);
  fullScreen();
  background(255);
  // I know that the first port in the serial list on my mac
  // is Serial.list()[0].
  // On Windows machines, this generally opens COM1.
  // Open whatever port is the one you're using.
  println(Serial.list());
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
  seed_images[1] = img1;
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
  d1 = minim.loadFile("1.wav", 2048);
  d2 = minim.loadFile("2.mp3", 2048);
  d3 = minim.loadFile("3.wav", 2048);
  d4 = minim.loadFile("4.wav", 2048);
  d5 = minim.loadFile("5.wav", 2048);
  d6 = minim.loadFile("6.wav", 2048);
  d7 = minim.loadFile("7.mp3", 2048);
  d8 = minim.loadFile("8.wav", 2048);
  fox.loop();
  wave.loop();
  noise.loop();
  d1.loop();
  d2.loop();
  d3.loop();
  d4.loop();
  d5.loop();
  d6.loop();
  d7.loop();
  d8.loop();
  noise.setGain(10);
  
  fox.setGain(-50);
  wave.setGain(-50);
  d1.setGain(-50);
  d2.setGain(-50);
  d3.setGain(-50);
  d4.setGain(-50);
  d5.setGain(-50);
  d6.setGain(-50);
  d7.setGain(-50);
  d8.setGain(-50);
  
  sound_mapping[0] = d1;
  sound_mapping[1] = d2;
  sound_mapping[2] = d3;
  sound_mapping[3] = d4;
  sound_mapping[4] = d5;
  sound_mapping[5] = fox;
  sound_mapping[6] = d6;
  sound_mapping[7] = d7;
  sound_mapping[8] = d8;
  sound_mapping[9] = wave;
}

void draw() {
  background(bg);
  
  if ( myPort.available() > 0) {  // If data is available,
    val = myPort.readStringUntil('\n');         // read it and store it in val
  }

  color(0);
  if (val != null && val.strip().split("-").length == 2) {
    //println(val.strip().split("-")[0]);
    int x = int(val.strip().split("-")[0]);
    int y = int(val.strip().split("-")[1]);
    posY = int(map(x, 0, 1023, 0, height));
    posX = int(map(y, 0, 1023, width, 0));
  }
  
  line(0, posY, width, posY);
  line(posX, 0, posX, height);
  
  
  // process sound map -----
 
  Integer[] ids2;
  Integer[] ids1;
  Integer[] ids;
  
  int area_for_sound_2 = 50;
  ids2 = checkImageFound(posX, posY, area_for_sound_2);
  setGlobalGains(ids2, -7);
  
  int area_for_sound_1 = 30;
  ids1 = checkImageFound(posX, posY, area_for_sound_1);
  setGlobalGains(ids1, -5);
  if (ids1.length > 0 && insertNormalImage) { // reset flag for inserting normal images when entering a normal image.
    insertNormalImage = false;
    try {
      Files.copy(Paths.get(sourceNormal + getNextNormalImageId()+".jpeg"), 
                              Paths.get(dest + getNextNormalImageId()+".jpeg"), 
                              StandardCopyOption.REPLACE_EXISTING);
    } catch (IOException e) {
        print(e);
    }
  }
  
  int area_for_sound_0 = 10;
  ids = checkImageFound(posX, posY, area_for_sound_0);
  setGlobalGains(ids, 10);
  if (ids.length > 0) { // reset flag for inserting normal images when entering a seed image.
    insertNormalImage = false;
  }
  
  // silence all not found images
  Integer allFound[] = (Integer[]) concat(ids, ids1);
  if (allFound.length < 1) {
    if (seedImageFound) { //hack for doing this only once
      try {
        Files.copy(Paths.get(sourceNormal + getNextNormalImageId()+".jpeg"), 
                                Paths.get(dest + getNextNormalImageId()+".jpeg"), 
                                StandardCopyOption.REPLACE_EXISTING);
      } catch (IOException e) {
          print(e);
      }
    }
    insertNormalImage = true; // reset flag for inserting normal images when no images found.
    seedImageFound = false; // reset seed image flag when no images found.
  }
  
  for(int i=0; i<sound_mapping.length; i++) {
    boolean ffound = false;
    for (int j=0; j<allFound.length; j++) {
      if (i == allFound[j]) {
        ffound = true;
        break;
      }
    }
    
    if (!ffound) {
      sound_mapping[i].setGain(-80);
    }
  }
  
  // process image finding -------
  
  Integer[] image_ids = checkImageFound(posX, posY, area_for_image_found); 
  
  if (image_ids.length > 0) {
    image_found_counter = IMAGE_FOUND_INI;
    last_image_id = image_ids[0]; // only one image can be found actually.
    image(seed_images[last_image_id], img_coord[last_image_id][0], img_coord[last_image_id][1], img_size, img_size);
    // copy seed image
    if (!seedImageFound) {
      try {
        Files.copy(Paths.get(sourceSeed + last_image_id + ".png"), 
                                Paths.get(dest + last_image_id + ".png"), 
                                StandardCopyOption.REPLACE_EXISTING);
      } catch (IOException e) {
          print(e);
      }
      seedImageFound = true;
    }
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
      noise.shiftGain(noise.getGain(), -50, 2000);
      gainShifting = true;
    } else {
      gainShifting = false;
    }
  } else {
    img_size = 128;
    
    if (noise.getGain() < 10) {
      noise.shiftGain(noise.getGain(), 10, 1000);
      gainShifting = true;
    } else {
      gainShifting = false;
    }
  }
  
  // ----------
  
}

int getNextNormalImageId() {
  if (normalImageId >= NORMAL_IMAGES_GAP) {
    normalImageId = 0;
  } else {
    normalImageId++;
  }
  return normalImageId;
}

void setGlobalGains(Integer[] ids, int gain) {
  
  //break found and not found sounds and set gain accordingly
  ArrayList<Integer> found = new ArrayList<Integer>();
  ArrayList<Integer> notFound = new ArrayList<Integer>();
  
  for (int k=0; k<sound_mapping.length; k++) {
    boolean ffound = false;
    for (int j=0; j<ids.length; j++) {
      if (k == ids[j]) { // ids[j] has been found
        ffound = true;
        break;
      }
    }
    
    if (ffound) {
      found.add(k);
    } else {
      notFound.add(k);
    }
  }
  
  // turn on found images sounds
  for (int f: found) { //<>//
    sound_mapping[f].shiftGain(sound_mapping[f].getGain(), gain, 100);
  }
  
  //// turn down not found images
  //for (int f: notFound) {
  //  sound_mapping[f].shiftGain(sound_mapping[f].getGain(), -50, 1000);
  //}
}

Integer[] checkImageFound(int posX, int posY, int area) {
  ArrayList<Integer> found_img_ids = new ArrayList<Integer>();
  for (int i=0; i<img_coord.length; i++) {
    if (abs(img_coord[i][0] - posX) <= area && abs(img_coord[i][1] - posY) <= area) {
      //println("found:" + i); //<>//
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
