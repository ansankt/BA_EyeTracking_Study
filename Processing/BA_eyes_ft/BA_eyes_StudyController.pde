EyeRenderer eyeRenderer;

void setup() {
  size(800, 800);
  eyeRenderer = new EyeRenderer();
}

void draw() {
  eyeRenderer.clear();
  eyeRenderer.drawCenteredEyes();
}
