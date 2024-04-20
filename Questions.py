import random

class TriviaQuestions:
    def __init__(self):
        self.trivia_questions = [
            {"question": "The Israeli Air Force was the first to use the F-35 in combat operations.", "answer": ["Y", "T", "1"]},
            {"question": "Israel's Air Force was officially established in late May 1948, shortly after the country declared independence.", "answer": ["Y", "T", "1"]},
            {"question": "The Israeli Air Force played a crucial role in Operation Opera, which targeted a nuclear reactor in Iraq.", "answer": ["Y", "T", "1"]},
            {"question": "The Israeli Air Force has developed its own satellite system for reconnaissance.", "answer": ["Y", "T", "1"]},
            {"question": "Israel was the first country to develop drone technology for military use.", "answer": ["Y", "T", "1"]},
            {"question": "The Israeli Air Force conducted one of the longest-range fighter missions in history to Uganda in 1976.", "answer": ["Y", "T", "1"]},
            {"question": "The Israeli Air Force has a unique unit specializing in helicopter missions called Unit 669.", "answer": ["Y", "T", "1"]},
            {"question": "Israel’s Air Force runs a youth program called 'The Sky is the Limit' to train future pilots.", "answer": ["Y", "T", "1"]},
            {"question": "The Israeli Air Force has an operational fleet of Arrow missile systems.", "answer": ["Y", "T", "1"]},
            {"question": "Israel's Air Force uses advanced AI technologies for real-time mission management.", "answer": ["Y", "T", "1"]},

            # False but plausible statements
            {"question": "The Israeli Air Force operates a fleet of stealth bombers.", "answer": ["N", "F", "0"]},
            {"question": "Israel's Air Force was officially established before the state of Israel was declared in 1948.", "answer": ["N", "F", "0"]},
            {"question": "Israel is the only country in the Middle East with an astronaut corps within its Air Force.", "answer": ["N", "F", "0"]},
            {"question": "The Israeli Air Force has more fighter jets than the UK Royal Air Force.", "answer": ["N", "F", "0"]},
            {"question": "The Israeli Air Force uses a unique desert camouflage for all its aircraft.", "answer": ["N", "F", "0"]},
            {"question": "The Israeli Air Force operates an underwater base in the Mediterranean Sea for intelligence gathering.", "answer": ["N", "F", "0"]},
            {"question": "Israel's Air Force developed a missile system called 'Sky Shield' that can neutralize nuclear missiles.", "answer": ["N", "F", "0"]},
            {"question": "The Israeli Air Force has a space division responsible for launching military satellites.", "answer": ["N", "F", "0"]},
            {"question": "The Israeli Air Force employs a special breed of camels for desert reconnaissance missions.", "answer": ["N", "F", "0"]},
            {"question": "Israel developed a technology that allows fighter jets to become invisible to radar.", "answer": ["N", "F", "0"]},
        ]
        self.curr_question = None

    def get_trivia_question(self):
        self.curr_question = random.choice(self.trivia_questions)
        return self.curr_question["question"]

    def check_trivia_answer(self, user_answer):
        return user_answer in self.curr_question["answer"]

    def get_trivia_answer(self):
        return self.curr_question["answer"]

    def get_trivia_question_dict(self):
        return random.choice(self.trivia_questions)

