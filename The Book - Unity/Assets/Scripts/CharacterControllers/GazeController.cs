using UnityEngine;

public class GazeController : MonoBehaviour
{
    [SerializeField]
    Transform m_target;

    [SerializeField]
    Transform m_headTransform;

    [SerializeField]
    Vector3 m_headRotationCorrection;

    [SerializeField]
    float m_fireflySpeed;

    [SerializeField]
    Transform m_headLookAtFirefly;

    public void LockTarget(Transform target)
    {
        m_target = target;
    }
    public void ClearTarget()
    {
        m_target = null;
    }

    private void Update()
    {
        if (m_target != null)
        {
            Vector3 targetDirection = m_target.position - m_headLookAtFirefly.position;
            m_headLookAtFirefly.position = m_headLookAtFirefly.position + targetDirection * Time.deltaTime * m_fireflySpeed;
        }
    }

    void LateUpdate()
    {
        if (m_target != null)
        {
            m_headTransform.LookAt(m_headLookAtFirefly.position);
            m_headTransform.Rotate(m_headRotationCorrection);
            //Logger.Log("SimpleLookAt", $"TargetPOI: {m_realisticEyeController.TargetPOI.name} Head: {m_headTransform.rotation.ToString()}", Logger.Level.Debug);
        }
    }
}
