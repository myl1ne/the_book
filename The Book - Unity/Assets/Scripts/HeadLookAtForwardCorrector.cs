using RealisticEyeMovements;
using UnityEngine;

public class HeadLookAtForwardCorrector : MonoBehaviour
{
    [SerializeField]
    LookTargetController m_realisticEyeController;

    [SerializeField]
    Transform m_headTransform;

    [SerializeField]
    Vector3 m_headRotationCorrection;

    [SerializeField]
    float m_fireflySpeed;

    [SerializeField]
    Transform m_headLookAtFirefly;

    // Start is called before the first frame update
    void Start()
    {

    }

    private void Update()
    {
        if (m_realisticEyeController.TargetPOI != null)
        {
            Vector3 targetDirection = m_realisticEyeController.TargetPOI.gameObject.transform.position - m_headLookAtFirefly.position;
            m_headLookAtFirefly.position = m_headLookAtFirefly.position + targetDirection * Time.deltaTime * m_fireflySpeed;
        }
    }

    void LateUpdate()
    {
        if (m_realisticEyeController.TargetPOI != null)
        {
            m_headTransform.LookAt(m_headLookAtFirefly.position);
            m_headTransform.Rotate(m_headRotationCorrection);
            //Logger.Log("SimpleLookAt", $"TargetPOI: {m_realisticEyeController.TargetPOI.name} Head: {m_headTransform.rotation.ToString()}", Logger.Level.Debug);
        }
    }
}