using Newtonsoft.Json.Linq;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using static NativeBridge.SDK;

/// <summary>
/// Catches input events that we want to expose to the native environment
/// </summary>
public class InputToNative : MonoBehaviour
{
    void Update()
    {
        CheckAndBroadcastClickedEntity();
    }

    private void CheckAndBroadcastClickedEntity()
    {
        Ray? ray = null;
        if (Input.touchCount > 0)
        {
            Touch touch = Input.touches[0];
            ray = Camera.main.ScreenPointToRay(touch.position);
        }
        else if (Input.mousePresent && Input.GetMouseButtonDown(0))
        {
            ray = Camera.main.ScreenPointToRay(Input.mousePosition);
        }
        if (ray != null)
        {
            RaycastHit hit;

            if (Physics.Raycast(ray.Value, out hit))
            {
                Entity ent = null;
                if (hit.transform.gameObject.TryGetComponent<Entity>(out ent))
                {
                    NativeBridge.SendSerializedEvent(new EntityEventOnClick() { entityName = ent.name});
                }
            }
        }
    }
}
