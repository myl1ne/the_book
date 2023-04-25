using UnityEngine;
using UnityEngine.AI;

[RequireComponent(typeof(NavMeshAgent))]
public class MotionController : MonoBehaviour
{
    public enum MotionState { Standing, Walking, Running }
    private MotionState m_motionState = MotionState.Standing;
    private NavMeshAgent m_navMeshAgent;

    [SerializeField]
    private Transform m_target;
    [SerializeField]
    private float m_walkSpeed = 10f;
    [SerializeField]
    private float m_runSpeed = 20f;
    [SerializeField]
    private float m_walkDistanceLowerRange = 10f;
    [SerializeField]
    private float m_runDistanceLowerRange = 30f;

    [SerializeField]
    private Animator m_animator;

    private void Start()
    {
        m_navMeshAgent = GetComponent<NavMeshAgent>();
    }

    public void SetTarget(Transform target)
    {
        m_target = target;
    }

    public void ClearTarget()
    {
        m_target = null;
    }

    private void Update()
    {
        UpdateMotionState();
        MoveAgent();
    }

    private void UpdateMotionState()
    {
        if (m_target == null)
        {
            m_motionState = MotionState.Standing;
            return;
        }

        float distanceToTarget = Vector3.Distance(transform.position, m_target.position);

        if (distanceToTarget < m_walkDistanceLowerRange)
        {
            m_motionState = MotionState.Standing;
        }
        else if (distanceToTarget >= m_walkDistanceLowerRange && distanceToTarget < m_runDistanceLowerRange)
        {
            m_motionState = MotionState.Walking;
        }
        else
        {
            m_motionState = MotionState.Running;
        }
    }


    private void MoveAgent()
    {
        switch (m_motionState)
        {
            case MotionState.Standing:
                m_navMeshAgent.speed = 0f;
                m_animator?.SetBool("Walk", false);
                m_animator?.SetBool("Run", false);
                break;

            case MotionState.Walking:
                m_navMeshAgent.speed = m_walkSpeed;
                m_animator?.SetBool("Walk", true);
                m_animator?.SetBool("Run", false);
                break;

            case MotionState.Running:
                m_navMeshAgent.speed = m_runSpeed;
                m_animator?.SetBool("Walk", false);
                m_animator?.SetBool("Run", true);
                break;
        }

        if (m_target != null)
        {
            m_navMeshAgent.SetDestination(m_target.position);
        }
    }
}
