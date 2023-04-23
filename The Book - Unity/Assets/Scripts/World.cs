using Sirenix.OdinInspector;
using System;
using System.Collections.Generic;
using UnityEngine;

/// <summary>
/// Handles a collection of entities.
/// 3D and 2D entities are separated: 2D entities are rendered in a screen overlay, 3D entities are objects in the scene.
/// </summary>
public class World : SerializedMonoBehaviour
{
    /// <summary>
    /// Prefabs to instantiate for specific names of entities (e.g. Miroka, Rune)
    /// </summary>
    [SerializeField]
    Dictionary<string, Entity> m_prefabs_by_name;

    /// <summary>
    /// The transform that will be used to hold 3D entities.
    /// </summary>
    [SerializeField]
    Transform m_entities3DParent;

    /// <summary>
    /// The transform that will be used to hold 2D entities.
    /// </summary>
    [SerializeField]
    Transform m_entities2DParent;

    /// <summary>
    /// Contains all the entities known by the world.
    /// We use this instead of any logic on the transform children.
    /// </summary>
    Dictionary<string, Entity> m_entities = new Dictionary<string, Entity>();

    /// <summary>
    /// On start we parse all the entities trees and updated m_entities from them
    /// </summary>
    private void Start()
    {
        foreach (Transform t in m_entities3DParent)
        {
            try
            {
                var ent = t.GetComponent<Entity>();
                ent.m_name = t.name;
                m_entities.Add(t.gameObject.name, ent);
            }
            catch (Exception e)
            {
                Logger.Log("World", $"While populating entities from scene: {e.ToString()}", Logger.Level.Error);
            }
        }
        NativeBridge.SendSerializedEvent(new NativeBridge.SDK.WorldEventOnCreated());
    }

    /// <summary>
    /// Tabula Rasa
    /// </summary>
    public void Clear()
    {
        var entitiesKeys = new List<string>(m_entities.Keys);
        foreach (var e in entitiesKeys)
        {
            DeleteEntity(e);
        }
    }

    /// <summary>
    /// Remove an entity from the world by its name
    /// </summary>
    /// <param name="name">Entity to delete</param>
    public void DeleteEntity(string name)
    {
        Destroy(m_entities[name].gameObject);
        m_entities.Remove(name);
    }

    /// <summary>
    /// Updates and entity with new data if it exists already, if not create it.
    /// </summary>
    /// <param name="data"></param>
    public void CreateOrUpdateEntity(Entity.Data data)
    {
        Entity ent = null;
        if (!m_entities.ContainsKey(data.name))
        {
            Entity prefab = null;
            if (data.prefabName == null)
            {
                data.prefabName = data.entityType == Entity.EntityType.TwoD ? "Generic2D" : "Generic3D";
            }
            if (m_prefabs_by_name.ContainsKey(data.prefabName))
            {
                prefab = m_prefabs_by_name[data.prefabName];
            }

            Transform parent = prefab.getTypeForPrefab() == Entity.EntityType.TwoD?m_entities2DParent:m_entities3DParent;
            ent = Instantiate(prefab, parent);
            ent.m_name = data.name;
            m_entities.Add(data.name, ent);
        } 
        else
        {
            ent = m_entities[data.name];
        }
        ent.UpdateData(data);
    }

    /// <summary>
    /// Get an entity by name
    /// </summary>
    /// <param name="name">The name of the entity to retrieve</param>
    public Entity GetEntityByName(string name)
    {
        if (!m_entities.ContainsKey(name))
        {
            return null;
        }
        return m_entities[name];
    }
}
