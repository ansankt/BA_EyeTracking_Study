class Trial {
  int id;
  String condition;
  Question[] questions;

  Trial(int id, String condition, Question[] questions) {
    this.id = id;
    this.condition = condition;
    this.questions = questions;
  }
}
