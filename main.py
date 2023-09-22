import os

import six
from google.cloud import speech
from google.cloud import language_v1
import PySimpleGUI as sg
import speech_recognition as sr

def transcribe_file(speech_file):
    client = speech.SpeechClient()

    from pydub import AudioSegment
    from pydub.effects import normalize

    # Import target audio file
    loud_then_quiet = AudioSegment.from_file(speech_file)

    # Normalize target audio file
    normalized_loud_then_quiet = normalize(loud_then_quiet)
    normalized_loud_then_quiet.export("normalizedAudio.wav", format="wav")
    #r = sr.Recognizer()
    #r.recognize_google(normalized_loud_then_quiet)

    with open(speech_file, "rb") as audio_file:
        content = audio_file.read()

    """
     Note that transcription is limited to a 60 seconds audio file.
     Use a GCS file for audio longer than 1 minute.
    """
    audio = speech.RecognitionAudio(content=content)

    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=16000,
        language_code="en-US",
    )

    operation = client.long_running_recognize(config=config, audio=audio)

    print("Waiting for operation to complete...")
    response = operation.result(timeout=90)


    # Each result is for a consecutive portion of the audio. Iterate through
    # them to get the transcripts for the entire audio file.
    for result in response.results:
        # The first alternative is the most likely one for this portion.
        print("Transcript: {}".format(result.alternatives[0].transcript))
        print("Confidence: {}".format(result.alternatives[0].confidence))
        return format(result.alternatives[0].transcript)


def sample_analyze_sentiment(content):
    client = language_v1.LanguageServiceClient()

    # content = 'Your text to analyze, e.g. Hello, world!'

    if isinstance(content, six.binary_type):
        content = content.decode("utf-8")

    type_ = language_v1.Document.Type.PLAIN_TEXT
    document = {"type_": type_, "content": content}

    response = client.analyze_sentiment(request={"document": document})
    sentiment = response.document_sentiment
    print("Score: {}".format(sentiment.score))
    print("Magnitude: {}".format(sentiment.magnitude))
    return sentiment.score

def getVoiceFile():
    working_directory = os.getcwd()

    layout = [
        [sg.Text("Choose a Voice file:")],
        [sg.InputText(key="-FILE_PATH-"),
         sg.FileBrowse(initial_folder="C:/Users/Aravindh/PycharmProjects/VoiceBasedComplaints/VoiceRecordings",
                       file_types=[("JPEG images", "*.wav")])],
        [sg.Button('Submit'), sg.Exit()]
    ]

    window = sg.Window("VoiceBasedComplaints", layout)

    while True:
        event, values = window.read()
        if event in (sg.WIN_CLOSED, 'Exit'):
            break
        elif event == "Submit":
            path = values["-FILE_PATH-"]
            print(path)
            window.close()
            return path


def displaySentiment(sentiment):
    layout = [[sg.Text(sentiment, enable_events=True,
                        key='-TEXT-', font=('Arial Bold', 20),
                        expand_x=True, justification='center')],
              ]
    window = sg.Window('Hello', layout, size=(500, 75))
    while True:
        event, values = window.read()
        print(event, values)
        if event == sg.WIN_CLOSED or event == 'Exit':
            break
    window.close()

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    path = getVoiceFile()
    text = transcribe_file(path)
    path = path.split("/")
    outputPath = 'output/' + path[len(path) - 1] + '.txt'
    with open(outputPath, 'w', encoding="utf-8") as r:
        r.write(text)
    sentimentScore = sample_analyze_sentiment(text)
    if sentimentScore == 0:
        sentiment = "Neutral"
    elif sentimentScore > 0:
        sentiment = "Positive"
    elif sentimentScore < 0:
        sentiment = "Negative"
    displaySentiment(sentiment)

