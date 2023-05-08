using System;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using Sirenix.OdinInspector;
using Sirenix.Serialization;
using UnityEditor;
using static GazeController;

public class GazeController : SerializedMonoBehaviour
{
    [Serializable]
    public class LookAtTransform
    {
        public Transform m_transform;
        public float m_rotationSpeed = 1f;
        public Vector3 m_rotationOffset = Vector3.zero;
    }

    [Serializable]
    public class ConfigurableTransforms
    {
        public List<Vector3> m_positionConfigurations = new List<Vector3>();
        public List<Quaternion> m_rotationConfigurations = new List<Quaternion>();
    }

    [Serializable]
    public class EyeModel
    {
        public LookAtTransform m_eyeball;
        public Transform m_pupil;
        public List<Transform> m_eyelids = new List<Transform>();
        public ConfigurableTransforms m_eyeLidOpened = new ConfigurableTransforms();
        public ConfigurableTransforms m_eyeLidClosed = new ConfigurableTransforms();

        [Button("Save Opened")]
        public void SaveOpenedConfiguration()
        {
            SaveEyelidConfiguration(m_eyeLidOpened);
        }
        [Button("Load Opened")]
        public void LoadOpenedConfiguration()
        {
            LoadEyelidConfiguration(m_eyeLidOpened);
        }

        [Button("Save Closed")]
        public void SaveClosedConfiguration()
        {
            SaveEyelidConfiguration(m_eyeLidClosed);
        }
        [Button("Load Closed")]
        public void LoadClosedConfiguration()
        {
            LoadEyelidConfiguration(m_eyeLidClosed);
        }

        private void SaveEyelidConfiguration(ConfigurableTransforms eyelids)
        {
            List<Vector3> positions = new List<Vector3>();
            List<Quaternion> rotations = new List<Quaternion>();

            foreach (Transform t in m_eyelids)
            {
                positions.Add(t.localPosition);
                rotations.Add(t.localRotation);
            }

            eyelids.m_positionConfigurations = positions;
            eyelids.m_rotationConfigurations = rotations;
        }


        private void LoadEyelidConfiguration(ConfigurableTransforms eyelids)
        {
            List<Vector3> positions = eyelids.m_positionConfigurations;
            List<Quaternion> rotations = eyelids.m_rotationConfigurations;
            for (int i = 0; i < m_eyelids.Count; i++)
            {
                m_eyelids[i].localPosition = positions[i];
                m_eyelids[i].localRotation = rotations[i];
            }
        }
    }


    /// <summary>
    /// The chain of transforms/bones that are affected by the gaze
    /// </summary>
    [FoldoutGroup("Setup")]
    [SerializeField]
    private List<LookAtTransform> m_spineChain = new List<LookAtTransform>();

    /// <summary>
    /// All the eyes attached to the head model
    /// </summary>
    [FoldoutGroup("Setup")]
    [SerializeField]
    private List<EyeModel> m_eyes = new List<EyeModel>();


    [FoldoutGroup("Microsaccades")]
    [SerializeField]
    private float m_microsaccadeIntervalMin = 0.1f;
    [FoldoutGroup("Microsaccades")]
    [SerializeField]
    private float m_microsaccadeIntervalMax = 2.0f;
    [FoldoutGroup("Microsaccades")]
    [SerializeField]
    private float m_microsaccadeSphereRadius = 0.5f;
    private Vector3 m_microSaccadeNoise = Vector3.zero;

    [FoldoutGroup("Blink")]
    [SerializeField]
    private float m_blinkIntervalMin = 2f;
    [FoldoutGroup("Blink")]
    [SerializeField]
    private float m_blinkIntervalMax = 10f;

    /// <summary>
    /// The target that is being tracked by the gaze
    /// </summary>
    [FoldoutGroup("Attention")]
    [SerializeField]
    private Transform m_target;
    public Transform GetTarget() { return m_target; }

    public void LockTarget(Transform target)
    {
        m_target = target;
    }

    public void ClearTarget()
    {
        m_target = null;
    }

    private void Awake()
    {

    }

    private void Start()
    {
        StartCoroutine(BlinkCoroutine());
        StartCoroutine(MicroSaccadesCoroutine());
    }

    private void Update()
    {

    }

    void LateUpdate()
    {
        if (m_target != null)
        {
            //Control the eyes
            foreach (EyeModel e in m_eyes)
            {
                Vector3 noisyTarget = m_microSaccadeNoise + m_target.position;
                Vector3 targetDirection = noisyTarget - e.m_eyeball.m_transform.position;
                Quaternion targetRotation = Quaternion.LookRotation(targetDirection) * Quaternion.Euler(e.m_eyeball.m_rotationOffset); ;
                float step = e.m_eyeball.m_rotationSpeed * Time.deltaTime;
                e.m_eyeball.m_transform.rotation = Quaternion.Slerp(e.m_eyeball.m_transform.rotation, targetRotation, step);
            }

            //Control the spinal cord
            foreach (LookAtTransform lookAtTransform in m_spineChain)
            {
                Vector3 targetDirection = m_target.position - lookAtTransform.m_transform.position;
                Quaternion targetRotation = Quaternion.LookRotation(targetDirection) * Quaternion.Euler(lookAtTransform.m_rotationOffset);
                float step = lookAtTransform.m_rotationSpeed * Time.deltaTime;
                lookAtTransform.m_transform.rotation = Quaternion.Slerp(lookAtTransform.m_transform.rotation, targetRotation, step);
            }
        }
    }
    private IEnumerator MicroSaccadesCoroutine()
    {
        while (true)
        {
            float saccadeInterval = UnityEngine.Random.Range(m_microsaccadeIntervalMin, m_microsaccadeIntervalMax);
            m_microSaccadeNoise = UnityEngine.Random.insideUnitSphere *m_microsaccadeSphereRadius;
            yield return new WaitForSeconds(saccadeInterval);
        }
    }

    private IEnumerator BlinkCoroutine()
    {
        while (true)
        {
            float blinkInterval = UnityEngine.Random.Range(m_blinkIntervalMin, m_blinkIntervalMax);
            yield return new WaitForSeconds(blinkInterval);

            float blinkDuration = 0.1f;
            yield return Blink(blinkDuration);
        }
    }

    private IEnumerator Blink(float duration)
    {
        float elapsedTime = 0f;
        while (elapsedTime < duration)
        {
            elapsedTime += Time.deltaTime;
            float t = elapsedTime / duration;

            foreach (EyeModel e in m_eyes)
            {
                for (int i = 0; i < e.m_eyelids.Count; i++)
                {
                    if (t< 0.5f)
                    {
                        e.m_eyelids[i].localPosition = Vector3.Lerp(e.m_eyeLidOpened.m_positionConfigurations[i], e.m_eyeLidClosed.m_positionConfigurations[i], t * 2f);
                        e.m_eyelids[i].localRotation = Quaternion.Lerp(e.m_eyeLidOpened.m_rotationConfigurations[i], e.m_eyeLidClosed.m_rotationConfigurations[i], t * 2f);
                    }
                    else
                    {
                        e.m_eyelids[i].localPosition = Vector3.Lerp(e.m_eyeLidClosed.m_positionConfigurations[i], e.m_eyeLidOpened.m_positionConfigurations[i], (t - 0.5f) * 2f);
                        e.m_eyelids[i].localRotation = Quaternion.Lerp(e.m_eyeLidClosed.m_rotationConfigurations[i], e.m_eyeLidOpened.m_rotationConfigurations[i], (t - 0.5f) * 2f);
                    }
                }
            }
            yield return null;
        }
    }
}
