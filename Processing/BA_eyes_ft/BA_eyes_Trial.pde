class Trial {
  int id;
  String condition;
  int questionCount;
  int completedQuestions = 0;

  Trial(int id, String condition, int questionCount) {
    this.id = id;
    this.condition = condition;
    this.questionCount = questionCount;
  }

  void completeQuestion() {
    completedQuestions = min(completedQuestions + 1, questionCount);
  }

  boolean isComplete() {
    return completedQuestions >= questionCount;
  }
}
