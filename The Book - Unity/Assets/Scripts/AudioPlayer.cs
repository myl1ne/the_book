using System;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Networking;

public class AudioPlayer : MonoBehaviour
{
    /// <summary>
    /// The default audio source for when entities don't have an audio source.
    /// </summary>
    [SerializeField]
    private AudioSource m_fallbackAudioSource;
    public AudioSource fallbackAudioSource { get { return m_fallbackAudioSource; } }

    /// <summary>
    /// Play an audio clip from a URL
    /// </summary>
    /// <param name="audioSource"></param>
    /// <param name="audioUrl"></param>
    /// <returns></returns>
    public static IEnumerator PlayAudio(
        AudioSource audioSource,
        string audioUrl,
        Action onStart,
        Action onEnd
    )
    {
        if (audioSource == null)
        {
            audioSource = FindObjectOfType<AudioPlayer>().fallbackAudioSource;
        }
        using (UnityWebRequest request = UnityWebRequestMultimedia.GetAudioClip(audioUrl, AudioType.WAV))
        {
            yield return request.SendWebRequest();
            if (request.result == UnityWebRequest.Result.ConnectionError || request.result == UnityWebRequest.Result.ProtocolError)
            {
                Debug.LogError($"Error: {request.error}");
            }
            else
            {
                AudioClip audioClip = DownloadHandlerAudioClip.GetContent(request);
                audioSource.clip = audioClip;
                onStart?.Invoke();
                audioSource.Play();
                while (audioSource.isPlaying)
                {
                    yield return null;
                }
                onEnd?.Invoke();
            }
        }
    }
}
