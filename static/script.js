let recognition;

function translateText(text) {
  const targetLanguage = document.getElementById("targetLanguage").value;
  const sourceLanguage = document.getElementById("sourceLanguage").value;
  const translationModel = document.getElementById("translationModel").value;

  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open("POST", "/translate-text", true);
    xhr.setRequestHeader("Content-Type", "application/json;charset=UTF-8");

    xhr.onload = function () {
      if (xhr.status === 200) {
        const response = JSON.parse(xhr.responseText);

        if (response.hasOwnProperty("translation")) {
          resolve(response.translation);
        } else {
          reject(
            "Translation response does not contain 'translation' property"
          );
        }
      } else {
        reject(`Translation failed with status ${xhr.status}`);
      }
    };

    xhr.onerror = function () {
      reject("Network error occurred during translation");
    };

    const data = {
      text: text,
      target_language: targetLanguage,
      source_language: sourceLanguage,
      translation_model: translationModel,
    };

    xhr.send(JSON.stringify(data));
  });
}

function saveToFile(filename, content) {
  const blob = new Blob([content], { type: "text/plain" });
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = filename;
  link.click();
}

document.addEventListener("DOMContentLoaded", function () {
  recognition = window.webkitSpeechRecognition || window.SpeechRecognition;

  if (!recognition) {
    console.error("Speech recognition is not supported in this browser.");
    return;
  }

  recognition = new recognition();
  recognition.continuous = true;
  recognition.interimResults = true;
  recognition.lang = "en";

  recognition.onresult = function (event) {
    let interimTranscript = "";

    for (let i = event.resultIndex; i < event.results.length; ++i) {
      interimTranscript += event.results[i][0].transcript;
    }

    document.getElementById("transcription").innerText =
      "Interim: " + interimTranscript;

    if (interimTranscript.trim() !== "") {
      translateText(interimTranscript)
        .then((translation) => {
          document.getElementById("originalText").innerText =
            "Original: " + interimTranscript;
          document.getElementById("translatedText").innerText =
            "Translation: " + translation;

          displayTranslationOverlay(translation);
        })
        .catch((error) => {
          console.error("Translation error:", error);
        });
    }
  };
});

function startTranslation() {
  if (!recognition) {
    console.error("Speech recognition is not available.");
    return;
  }

  if (recognition && recognition.isStarted) {
    console.log("Speech recognition is already active.");
    return;
  }

  let sourceLanguage = document.getElementById("sourceLanguage").value;
  let targetLanguage = document.getElementById("targetLanguage").value;

  recognition.lang = sourceLanguage;
  recognition.start();

  recognition.isStarted = true;

  recognition.onend = function () {
    console.log("Speech recognition ended");
    recognition.isStarted = false;
  };
}

function stopTranslation() {
  if (recognition) {
    recognition.stop();
  } else {
    console.error("Speech recognition is not available.");
  }
}
