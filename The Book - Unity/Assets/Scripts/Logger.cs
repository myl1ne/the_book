using UnityEngine;

public static class Logger
{
    public enum Level { Debug = 0, Warning = 1, Error = 2 }
    public static void Log(string tag, string msg, Level level)
    {
        var logMsg = $"[{tag}]: {msg}";
        switch (level)
        {
            case Level.Debug:
                Debug.Log(logMsg);
                break;

            case Level.Warning:
                Debug.LogWarning(logMsg);
                break;

            case Level.Error:
                Debug.LogError(logMsg);
                break;
        }
    }
}
