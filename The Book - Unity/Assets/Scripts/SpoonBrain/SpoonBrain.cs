using System.Collections;
using UnityEngine;
using UnityEngine.Networking;
using Sirenix.OdinInspector;
using System.Collections.Generic;
using System;
using Newtonsoft.Json;

public class SpoonBrain : SerializedMonoBehaviour
{
    private string m_spoonBrainUrl = "https://spoon-brain.dev.spoon-cloud.com";
    public string spoonBrainUrl { get { return m_spoonBrainUrl; } set { m_spoonBrainUrl = value; } }

    #region LLM
    [SerializeField, FoldoutGroup("OpenAI Settings")]
    private string openAIKey = "your_api_key";

    public string OpenAIKey
    {
        get => openAIKey;
        set => openAIKey = value;
    }

    [FoldoutGroup("OpenAI Settings"), LabelText("Chat History")]
    [SerializeField, ListDrawerSettings(ShowIndexLabels = true, ListElementLabelName = "content")]
    private ChatHistoryLibrary.ChatHistoryEntry chatHistory = new ChatHistoryLibrary.ChatHistoryEntry();

    [Button("Call GPT Model", ButtonSizes.Large), FoldoutGroup("OpenAI Settings")]
    public void CallGptModel()
    {
        StartCoroutine(CallGptModelCoroutineWithChatHistory(chatHistory, (response) =>
        {
            Debug.Log("GPT Model response: " + response);
        }
        ));
    }

    public void CallGptModel(string prompt, System.Action<string> onResponseReceived)
    {
        ChatHistoryLibrary.ChatHistoryEntry chatMessages = new ChatHistoryLibrary.ChatHistoryEntry() {
            name = "Temporary",
            messages = new List<ChatHistoryLibrary.ChatMessage>()
            {
                new ChatHistoryLibrary.ChatMessage() { role = "user", content = prompt  }
            }
        };
        StartCoroutine(CallGptModelCoroutineWithChatHistory(chatMessages, onResponseReceived));
    }

    private IEnumerator CallGptModelCoroutineWithChatHistory(ChatHistoryLibrary.ChatHistoryEntry chatHistory, System.Action<string> onResponseReceived)
    {
        string url = "https://api.openai.com/v1/chat/completions";
        string messagesJson = JsonConvert.SerializeObject(chatHistory.messages);
        string jsonBody = $"{{\"model\": \"gpt-3.5-turbo\", \"messages\": {messagesJson}}}";
        Logger.Log("SpoonBrain", $"Calling: {url}", Logger.Level.Debug);

        UnityWebRequest request = new UnityWebRequest(url, "POST");
        request.uploadHandler = new UploadHandlerRaw(System.Text.Encoding.UTF8.GetBytes(jsonBody));
        request.downloadHandler = new DownloadHandlerBuffer();
        request.SetRequestHeader("Content-Type", "application/json");
        request.SetRequestHeader("Authorization", $"Bearer {OpenAIKey}");

        yield return request.SendWebRequest();

        if (request.result == UnityWebRequest.Result.ConnectionError || request.result == UnityWebRequest.Result.ProtocolError)
        {
            Debug.LogError($"Error: {request.error}");
            onResponseReceived?.Invoke($"Error: {request.error}");
        }
        else
        {
            string response = request.downloadHandler.text;
            onResponseReceived?.Invoke(response);
        }
    }
    #endregion

    #region TTS
    [Button("Call TTS", ButtonSizes.Large), FoldoutGroup("TTS Settings")]
    public void TTS(AudioSource audioSource, string textToSay, string voice, string language, Action onStart, Action onEnd)
    {
        StartCoroutine(SpeakText(audioSource, textToSay, voice, language, onStart, onEnd));
    }

    private IEnumerator SpeakText(AudioSource audioSource, string textToSay, string voice, string language, Action onStart, Action onEnd)
    {
        string url = $"{this.m_spoonBrainUrl}/generation/tts/speak?voice={voice}&language={language}&text_to_say={UnityWebRequest.EscapeURL(textToSay)}";
        UnityWebRequest request = new UnityWebRequest(url, "POST");
        request.uploadHandler = new UploadHandlerRaw(new byte[0]); // Empty request body
        request.downloadHandler = new DownloadHandlerBuffer();
        request.SetRequestHeader("Content-Type", "application/x-www-form-urlencoded");
        request.SetRequestHeader("accept", "application/json");

        yield return request.SendWebRequest();

        if (request.result == UnityWebRequest.Result.ConnectionError || request.result == UnityWebRequest.Result.ProtocolError)
        {
            Debug.LogError($"Error: {request.error}");
        }
        else
        {
            string audioUrl = request.downloadHandler.text.Replace("\"", "");
            StartCoroutine(AudioPlayer.PlayAudio(audioSource, audioUrl, onStart, onEnd));
        }
    }

    #endregion

    #region Others
    public void GenerateVisual2D(string prompt, Action<string> onUrlAvailable)
    {
        StartCoroutine(GenerateVisual2DAsync(prompt,onUrlAvailable));

    }
    private IEnumerator GenerateVisual2DAsync(string prompt, Action<string> onUrlAvailable)
    {
        string encodedPrompt = UnityWebRequest.EscapeURL(prompt);
        string url = $"{this.m_spoonBrainUrl}/generation/visual/2D?user_input={encodedPrompt}";
        UnityWebRequest request = new UnityWebRequest(url, "POST");
        request.uploadHandler = new UploadHandlerRaw(new byte[0]); // Empty request body
        request.downloadHandler = new DownloadHandlerBuffer();
        request.SetRequestHeader("Content-Type", "application/x-www-form-urlencoded");
        request.SetRequestHeader("accept", "application/json");

        yield return request.SendWebRequest();

        if (request.result == UnityWebRequest.Result.ConnectionError || request.result == UnityWebRequest.Result.ProtocolError)
        {
            Debug.LogError($"Error: {request.error}");
        }
        else
        {
            string visual2DUrl = request.downloadHandler.text.Replace("\"", "");
            onUrlAvailable?.Invoke(visual2DUrl);
        }
    }
    #endregion
}
