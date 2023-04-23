using RealisticEyeMovements;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class SceneAssistantMain : MonoBehaviour
{
    public LookTargetController lookat;
    public Transform forcedLookAtTarget;

    // Start is called before the first frame update
    void Start()
    {
        
    }

    // Update is called once per frame
    void Update()
    {
        if (forcedLookAtTarget != null)
        {
            lookat.LookAtPoiDirectly(forcedLookAtTarget);
        }
        else
        {
            lookat.ClearLookTarget();
        }
    }
}
