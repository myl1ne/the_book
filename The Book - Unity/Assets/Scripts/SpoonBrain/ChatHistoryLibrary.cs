using System.Collections.Generic;
using UnityEngine;

[CreateAssetMenu(fileName = "ChatHistoryLibrary", menuName = "Chat History Library", order = 1)]
public class ChatHistoryLibrary : ScriptableObject
{
    [System.Serializable]
    public struct ChatMessage
    {
        public string role;
        public string content;
    }

    [System.Serializable]
    public struct ChatHistoryEntry
    {
        public string name;
        public List<ChatMessage> messages;
    }

    public List<ChatHistoryEntry> m_chatHistories;
}