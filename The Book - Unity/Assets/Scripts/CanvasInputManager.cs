using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.EventSystems;

public class CanvasInputManager : MonoBehaviour
{
    bool m_isMouseOverCanvas = false;

    public void HandleMouseOverEvent(bool isOver)
    {
        m_isMouseOverCanvas = isOver;
        Logger.Log("CanvasInputManager", $"OnMouseOverEvent={m_isMouseOverCanvas}", Logger.Level.Debug);
    }

    void Update()
    {
#if !UNITY_EDITOR && UNITY_WEBGL
            WebGLInput.captureAllKeyboardInput = m_isMouseOverCanvas;
#endif
    }
}
