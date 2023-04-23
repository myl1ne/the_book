using System;
using System.Collections;
using UnityEngine;
using UnityEngine.Networking;
using UnityEngine.UI;

/// <summary>
/// Represents anything that is part of the world.
/// </summary>
public class Entity : MonoBehaviour
{
    public enum EntityType { TwoD, ThreeD }
    /// <summary>
    /// This is set on the prefab. It should never be changed or accessed.
    /// </summary>
    [SerializeField]
    EntityType m_typeForData;
    public EntityType getTypeForPrefab() { return m_typeForData; }
    public string m_name { 
        get { return name; } 
        set { name = value; m_data.name = name; } 
    }

    [Serializable]
    public class Data
    {
        public string name;
        public EntityType entityType;
        public string? prefabName;
        public Vector3? position;
        public Vector3? scale;
        public Quaternion? rotation;
        public float? width;
        public float? height;
        public string? meshUrl;
        public string? textureUrl;
    }
    private Data m_data = new Data();

    public void Awake()
    {
        m_data.entityType = m_typeForData;
        UpdateDataFromEngine();
    }

    private void Update()
    {
        UpdateDataFromEngine();
    }

    /// <summary>
    /// Update the data fields to the values read in the game engine
    /// </summary>
    private void UpdateDataFromEngine()
    {
        if (m_data.entityType == EntityType.ThreeD)
        {
            m_data.position = transform.position;
            m_data.scale = transform.localScale;
            m_data.rotation = transform.rotation;
        }
        else if (m_data.entityType == EntityType.TwoD)
        {
            RectTransform rect = (transform as RectTransform);
            m_data.position = new Vector3(
                rect.anchoredPosition3D.x / Screen.width,
                rect.anchoredPosition3D.y / Screen.height,
                rect.anchoredPosition3D.z
            );
            m_data.width = rect.rect.width / Screen.width;
            m_data.height = rect.rect.height / Screen.height;
        }
        //URLs cannot be infered from material/mesh
    }

    public void UpdateData(Data newData)
    {
        if (m_data.name != newData.name)
        {
            throw new Exception("Name mismatch. This should not happen");
        }
        if (m_data.entityType != newData.entityType)
        {
            throw new Exception("Type mismatch. This should not happen");
        }

        if (m_data.entityType == EntityType.TwoD)
        {
            UpdateData2D(newData);
        } 
        else if (m_data.entityType == EntityType.ThreeD)
        {
            UpdateData3D(newData);
        }
    }

    private void UpdateData3D(Data newData)
    {

        if (newData.position != null)
        {
            m_data.position = newData.position;
            transform.position = m_data.position.Value;
        }
        if (newData.scale != null)
        {
            m_data.scale = newData.scale;
            transform.localScale = m_data.scale.Value;
        }
        if (newData.rotation != null)
        {
            m_data.rotation = newData.rotation;
            transform.rotation = m_data.rotation.Value;
        }

        if (newData.textureUrl != null)
        {
            m_data.textureUrl = newData.textureUrl;
            StartCoroutine(AssignUrlTextureToMat(GetComponent<Renderer>().material, newData.textureUrl));
        }
        if (newData.meshUrl != null)
        {
            m_data.meshUrl = newData.meshUrl;
            StartCoroutine(AssignUrlMesh(GetComponent<MeshFilter>().mesh, newData.meshUrl));
        }
    }

    private void UpdateData2D(Data newData)
    {
        RectTransform rectTransform = transform as RectTransform;
        if (newData.position != null)
        {
            m_data.position = newData.position;
            Vector3 anchoredPosition = new Vector3(
                newData.position.Value.x * Screen.width,
                newData.position.Value.y * Screen.height,
                newData.position.Value.z
            );
            rectTransform.anchoredPosition3D = anchoredPosition;
        }

        if (newData.width != null)
        {
            m_data.width = newData.width;
        }

        if (newData.height != null)
        {
            m_data.height = newData.height;
        }
        rectTransform.sizeDelta = new Vector2(m_data.width.Value * Screen.width, m_data.height.Value * Screen.height);


        if (newData.textureUrl != null)
        {
            StartCoroutine(AssignUrlTextureToRawImage(GetComponent<RawImage>(), newData.textureUrl));
        }
    }

    #region Download handlers
    IEnumerator AssignUrlMesh(Mesh mesh, string url)
    {
        throw new System.NotImplementedException();
    }

    IEnumerator AssignUrlTextureToMat(Material mat, string url)
    {
        // Load the texture from the URL using UnityWebRequestTexture
        using (UnityWebRequest uwr = UnityWebRequestTexture.GetTexture(url))
        {
            yield return uwr.SendWebRequest();

            if (uwr.result != UnityWebRequest.Result.Success)
            {
                Debug.LogError(uwr.error);
                yield break;
            }

            // Get the loaded texture from the download handler
            Texture2D texture = DownloadHandlerTexture.GetContent(uwr);

            // Assign the texture to the material's main texture property
            mat.mainTexture = texture;
        }
    }
    IEnumerator AssignUrlTextureToRawImage(RawImage img, string url)
    {
        // Load the texture from the URL using UnityWebRequestTexture
        using (UnityWebRequest uwr = UnityWebRequestTexture.GetTexture(url))
        {
            yield return uwr.SendWebRequest();

            if (uwr.result != UnityWebRequest.Result.Success)
            {
                Debug.LogError(uwr.error);
                yield break;
            }

            // Get the loaded texture from the download handler
            Texture2D texture = DownloadHandlerTexture.GetContent(uwr);

            // Assign the texture to the material's main texture property
            img.texture = texture;
        }
    }
    #endregion
}
