import processing.sound.*;


/* int background = 255;
int circleradius = 75;
float eye_y = 400;
int eye_distance = 300;

float eye_x_left = 250;
float eye_x_right;

float eyeCenterX = 250;
float eyeCenterY = 400;

float ellipseRadiusX = 250 / 2;
float ellipseRadiusY = 400 / 2;


float movementspeed = 3.0;

float target_x; //fürs rechte Auge links wird dementsprechend angepasst
float target_y;

boolean waiting = false;
int waitUntil = 0;
int waiting_time=0;



void setup(){
 background(background);
 size(800,800);
 
 eye_x_right = eye_x_left + eye_distance;
 
 strokeWeight(4);
 ellipse(250,400, 250, 400);
 ellipse(550,400, 250, 400);
 
 fill(0);
 circle(eye_x_left,eye_y, circleradius);
 
 fill(0);
 circle(eye_x_right,eye_y, circleradius);
 
 noFill();
 
 target_x = eye_x_left;
 target_y = eye_y;
 
}


void draw(){
  background(background);
  
  strokeWeight(4);
  ellipse(250,400, 250, 400);
  ellipse(550,400, 250, 400);
 
 
  moveEye(); 

  fill(0);
  draw_circle(eye_x_left,eye_y);
  draw_circle(eye_x_right,eye_y);
  noFill();
}

void moveEye(){
  
   if(waiting){
    if(millis() > waitUntil){
        waiting = false;

        //TODO: neues Ziel setzen
        rnd_new_target();
        rnd_newWaitTime();
        rnd_movementSpeed();
    }
  } else {
  
  float dx = target_x - eye_x_left;
  float dy = target_y - eye_y;

  float distance = sqrt(dx*dx + dy*dy);


if(distance < movementspeed){
    eye_x_left = target_x;

    eye_y = target_y;

    eye_x_right = eye_x_left + eye_distance;
    println("waiting... for " + waiting_time + "ms");
    print("movementspeed: "+movementspeed);

    waiting = true;
    waitUntil = millis() + waiting_time;
    return;
    

  }

    eye_x_left += (dx / distance) *movementspeed;
    eye_y += (dy / distance) * movementspeed;
    eye_x_right = eye_x_left + eye_distance;
    println("Eye at: "+eye_x_left+","+eye_y);  
    println("Moving to: "+target_x +","+target_y);
    println("distance: " + distance);
    println("dx: " + dx);
    println("dy: " + dy);
   
  
  }
  
}

void rnd_new_target(){
  //sets the new target position on an inner ellipse, so the eyes wouldnt get out of the border
  
  
  /* target_x = (int) random(125+circleradius/2, 375 - circleradius/2);
  target_y = (int) random(200+circleradius/2, 600 - circleradius/2); * /
  
  float centerX = 250;
  float centerY = 400;
  float radiusX = 250/2 - circleradius/2;
  float radiusY = 400/2 - circleradius/2;

  float angle = random(TWO_PI);
  float r = sqrt(random(1));

  target_x = centerX + cos(angle) * r * radiusX;
  target_y = centerY + sin(angle) * r * radiusY;
  
}

void rnd_newWaitTime(){
  waiting_time = (int) random(1000,5000);

}

void rnd_movementSpeed (){
movementspeed = random(1.5,6);
}


void draw_circle(float xpos, float ypos){

  circle(xpos,ypos, circleradius);
  
}
*/





//TODO: States der Augen, wenn die Mittelpunkte innerhalb eines Kreisesliegen über distance to midpoint > r, dann isses gaze wenn Mensch drauf schaut dann mutual gaze
