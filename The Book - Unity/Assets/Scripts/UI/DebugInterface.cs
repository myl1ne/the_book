using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class DebugInterface : MonoBehaviour
{
    [SerializeField]
    NativeBridge bridge;

    [SerializeField]
    RectTransform panel;

    [SerializeField]
    TMPro.TMP_InputField serializedMethodInput;

    public void TogglePanel()
    {
        panel.gameObject.SetActive(!panel.gameObject.activeSelf);
    }

    public void CallSerializedActionFromField()
    {
        bridge.CallSerializedMethod(serializedMethodInput.text);
    }
}
