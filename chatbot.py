from characterai import aiocai
import asyncio
import streamlit as st
from streamlit_chat import message
from config import Parameters
import uuid
import pyttsx3
import os

class InterviewBot:
    """
    Class representing the Interview chatbot.
    """
    char = 'f4hEGbw8ywUrjsrye03EJxiBdooy--HiOWgU2EiRJ0s'
    token = '67c42f8f986f526fe33a8630b9bdbbf97b219783'
    tts_engine = pyttsx3.init()

    async def start_chat(self):
        """
        Initialize and start a chat session with Character.AI.
        """
        try:
            client = aiocai.Client(self.token)
            me = await client.get_me()

            async with await client.connect() as chat:
                new_chat, first_message = await chat.new_chat(self.char, me.id)
                return chat, new_chat, first_message
        except Exception as e:
            st.write(f"An error occurred: {e}")
            return None, None, None

    def __init__(self) -> None:
        """
        Initialize the InterviewBot and its session state.
        """
        if 'questions' not in st.session_state:
            st.session_state['questions'] = []

        if 'answers' not in st.session_state:
            st.session_state['answers'] = []

        if 'interview_step' not in st.session_state:
            st.session_state['interview_step'] = 0

        self.session_state = st.session_state

    async def prepare_questions(self) -> None:
        """
        Prepare the interview by generating questions from Character.AI.
        """
        chat, new_chat, first_message = await self.start_chat()

        if chat is None:
            st.write("Failed to start chat with Character.AI.")
            return

        questions = [
            "Hi! It's nice to meet you. Let's start with something simple: What is your name?",
            "Great, thanks for that! Now, can you tell me why you're interested in this job?",
            "Awesome! I’d love to know more about the skills you bring to the table."
        ]
        self.session_state['questions'] = [(question, self._generate_uuid()) for question in questions]

    def _text_to_speech(self, text: str, filename: str) -> None:
        """
        Convert text to speech and save to a file.
        """
        self.tts_engine.save_to_file(text, filename)
        self.tts_engine.runAndWait()

    def ask_question(self) -> None:
        """
        Display the current question.
        """
        text, key = self.session_state['questions'][self.session_state['interview_step']]
        filename = f'question_{key}.wav'
        self._text_to_speech(text, filename)
        st.audio(filename, format='audio/wav')
        message(text, key=key)

    def get_answer(self) -> None:
        """
        Get and store the answer provided by the user.
        """
        answer = st.text_input("Your answer: ", key="input" + str(self.session_state['interview_step']))

        if answer:
            acknowledgements = [
                "Thanks for sharing that!",
                "Got it, that sounds interesting.",
                "Nice answer, let's keep going!"
            ]
            self.session_state['answers'].append((answer, self._generate_uuid()))
            st.write(acknowledgements[self.session_state['interview_step'] % len(acknowledgements)])
            self.session_state['interview_step'] += 1
            st.experimental_rerun()

    def display_past_questions_and_answers(self) -> None:
        """
        Display all past questions and their corresponding answers.
        """
        for i in range(self.session_state['interview_step']):
            question_text, question_key = self.session_state['questions'][i]
            filename = f'question_{question_key}.wav'
            self._text_to_speech(question_text, filename)
            st.audio(filename, format='audio/wav')
            message(question_text, key=question_key)

            if i < len(self.session_state['answers']):
                answer_text, answer_key = self.session_state['answers'][i]
                filename = f'answer_{answer_key}.wav'
                self._text_to_speech(answer_text, filename)
                st.audio(filename, format='audio/wav')
                message(answer_text, is_user=True, key=answer_key)

    async def evaluate_candidate(self) -> str:
        """
        Generate an evaluation for the candidate based on their answers to the interview questions.
        """
        chat, new_chat, first_message = await self.start_chat()

        if chat is None:
            st.write("Failed to start chat with Character.AI.")
            return ""

        interview_text = "".join([f"Question: {question}\nAnswer: {answer}\n" for (question, _), (answer, _) in zip(self.session_state['questions'], self.session_state['answers'])])
        response = await chat.send_message(self.char, new_chat.chat_id, interview_text)

        evaluation_text = f"Thanks for your responses! Based on what you’ve shared, here’s my take:\n\n{response.text}\n\nHope that was helpful!"
        return evaluation_text

    def execute_interview(self) -> None:
        """
        Execute the interview process.
        """
        self.display_past_questions_and_answers()

        if self.session_state['interview_step'] < len(self.session_state['questions']):
            self.ask_question()
            self.get_answer()

        elif self.session_state['interview_step'] == len(self.session_state['questions']):
            evaluation = asyncio.run(self.evaluate_candidate())
            filename = 'evaluation.wav'
            self._text_to_speech(evaluation, filename)
            st.audio(filename, format='audio/wav')
            st.write(f"Character.AI's evaluation: {evaluation}")
            self.session_state['interview_step'] += 1

    @staticmethod
    def _generate_uuid() -> str:
        """
        Generate a unique identifier.
        """
        return str(uuid.uuid4())


def create_bot() -> None:
    """
    Create an InterviewBot and manage its operation.
    """
    bot = InterviewBot()

    if len(bot.session_state['questions']) == 0:
        intro_text = "Hey there! I'm your friendly interviewer bot. I’ll ask you a few questions, and we’ll have a fun chat about your experience and skills. Let's get started!"
        filename = 'intro.wav'
        bot._text_to_speech(intro_text, filename)
        st.audio(filename, format='audio/wav')
        message(intro_text, key="greeting")
        asyncio.run(bot.prepare_questions())

    bot.execute_interview()


# Streamlit UI

st.title("InterviewBot - AI Interview Chatbot")

# Use Railway's dynamic port from the environment variable
port = int(os.environ.get('PORT', 8501))
st.set_option('server.port', port)
st.set_option('server.address', '0.0.0.0')

create_bot()
