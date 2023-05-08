using Sirenix.Serialization;
using System.Collections;
using System.Collections.Generic;
using System.Linq;
using UnityEngine;

public class AttentionController : MonoBehaviour
{
    [System.Serializable]
    public class AttentionTarget
    {
        public float m_saliency = 0.5f;
    }
    World m_world;

    [SerializeField]
    GazeController m_gaze;

    [OdinSerialize]
    Dictionary<Entity, AttentionTarget> m_attentionTargets = new Dictionary<Entity, AttentionTarget>();
    
    public float m_attentionRadius = 100.0f;
    public float m_saliencyBaseSpeed = 0.05f;
    private float m_lastAttentionSwitch = -1.0f;
    public float m_attentionSwitchCooldown = 1.0f;

    // Start is called before the first frame update
    void Start()
    {
        m_world = FindObjectOfType<World>();
    }

    // Update is called once per frame
    void Update()
    {
        UpdateSaliency();
    }

    private void UpdateSaliency()
    {
        //Get all world entities in range
        var entsInRange = m_world.GetEntitiesByDistance(transform, m_attentionRadius).ToDictionary(pair=>pair.Item1, pair=>pair.Item2);
        entsInRange.Remove(GetComponent<Entity>());
        List<Entity> leftRange = new List<Entity>();
        foreach (var existingTarget in m_attentionTargets.Keys)
        {
            if (!entsInRange.ContainsKey(existingTarget))
            {
                leftRange.Add(existingTarget);
            }
        }
        foreach (var target in leftRange)
        {
            m_attentionTargets.Remove(target);
            Logger.Log("AttentionController", $"{target.name} left range of {name}", Logger.Level.Debug);
        }

        List<Entity> gotInRange = new List<Entity>();
        foreach (var target in entsInRange.Keys)
        {
            if (!m_attentionTargets.ContainsKey(target))
            {
                gotInRange.Add(target);
                Logger.Log("AttentionController", $"{target.name} got in range of {name}", Logger.Level.Debug);
            }
        }
        foreach (var target in gotInRange)
        {
            m_attentionTargets.Add(target, new AttentionTarget());
        }

        //Update saliency & find best target
        var currentTarget = m_gaze.GetTarget();
        Entity maxTarget = null;
        foreach (var target in m_attentionTargets)
        {
            if (currentTarget && currentTarget.transform == target.Key.transform)
            {
                target.Value.m_saliency -= target.Value.m_saliency * m_saliencyBaseSpeed * Time.deltaTime;
            }
            else
            {
                target.Value.m_saliency += target.Value.m_saliency * m_saliencyBaseSpeed * Time.deltaTime;
            }
            target.Value.m_saliency = Mathf.Clamp01(target.Value.m_saliency);

            if (maxTarget == null || target.Value.m_saliency > m_attentionTargets[maxTarget].m_saliency)
            {
                maxTarget = target.Key;
            }
        }

        //Switch target if required
        if (maxTarget != null && maxTarget.transform != currentTarget.transform && (Time.time - m_lastAttentionSwitch) > m_attentionSwitchCooldown) 
        {
            Logger.Log("AttentionController", $"{name} is switching to {maxTarget.name}", Logger.Level.Debug);
            m_gaze.LockTarget(maxTarget.transform);
            m_lastAttentionSwitch = Time.time;
        }
    }
}
