using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using UnityEngine;
using System.Runtime.InteropServices;
using Sirenix.OdinInspector;
using UnityEngine.SceneManagement;
using static NativeBridge.SDK;
using System.Reflection;
using System;

public class NativeBridge : MonoBehaviour
{
    private void Start()
    {
        m_world = FindObjectOfType<World>();
        m_canvasInputManager = FindObjectOfType<CanvasInputManager>();
        m_spoonBrain = FindObjectOfType<SpoonBrain>();
    }

    #region Native Events (i.e Unity to Native)
    [DllImport("__Internal")]
    private static extern void NativeSendSerializedEvent(string eventName, string eventData);
    private static void SendSerializedEvent(string eventName, JObject eventData)
    {
        SendSerializedEventJsonStr(eventName, eventData.ToString());
    }
    private static void SendSerializedEventJsonStr(string eventName, string eventDataJsonStr)
    {
        Logger.Log("SendSerializedEvent", $"{eventName}\n\t==>{eventDataJsonStr}", Logger.Level.Debug);
        try
        {
            NativeSendSerializedEvent(eventName, eventDataJsonStr);
        }
        catch (System.Exception e)
        {
            Logger.Log("NativeBridge", $"Error while sending native event: {e.Message}", Logger.Level.Warning);
        }
    }
    public static void SendSerializedEvent(SerializedMethod serializedMethod)
    {
        try
        {
            SendSerializedEventJsonStr(serializedMethod.methodName, JsonUtility.ToJson(serializedMethod));
        }
        catch (System.Exception e)
        {
            Logger.Log("NativeBridge", $"Error while sending native event: {e.Message}", Logger.Level.Warning);
        }
    }

    #endregion

    #region Serialized Methods logic (i.e Native to Unity)

    #region Serialized methods & events (aka: SDK)
    [System.Serializable]
    public class SDK
    {
        [System.Serializable]
        public class SerializedMethod
        {
            public string methodName;
            public SerializedMethod()
            {
                methodName = GetType().Name;
            }
            public static TDerived CreateDerived<TDerived>(SerializedMethod baseInstance)
                where TDerived : SerializedMethod, new()
            {
                TDerived derivedInstance = new TDerived();

                BindingFlags bindingFlags = BindingFlags.Public |
                                             BindingFlags.NonPublic |
                                             BindingFlags.Instance |
                                             BindingFlags.Static;

                Type baseType = baseInstance.GetType();
                FieldInfo[] fields = baseType.GetFields(bindingFlags);

                foreach (FieldInfo field in fields)
                {
                    if (field.Name == "methodName")
                        continue;
                    object value = field.GetValue(baseInstance);
                    field.SetValue(derivedInstance, value);
                }

                return derivedInstance;
            }
        }

        #region World

        [System.Serializable]
        public class WorldActionClear : SerializedMethod
        { }

        [System.Serializable]
        public class WorldActionCreateOrUpdateEntity : SerializedMethod
        {
            public Entity.Data entityData;
        }
        public class WorldEventOnCreated : SerializedMethod
        { }
        #endregion

        #region Entity Methods
        public class EntitySerializedMethod : SerializedMethod
        {
            public string entityName;
        }
        #region TTS
        [System.Serializable]
        public class EntityActionSay : EntitySerializedMethod
        {
            public string voice;
            public string language;
            public string text;
        }

        [System.Serializable]
        public class EntityEventSayOnStart : EntityActionSay
        { }

        [System.Serializable]
        public class EntityEventSayOnEnd : EntityActionSay
        { }

        public class EntityActionPlaySound : EntitySerializedMethod
        {
            public string soundUrl;
        }

        [System.Serializable]
        public class EntityEventPlaySoundOnStart : EntityActionPlaySound
        { }

        [System.Serializable]
        public class EntityEventPlaySoundOnEnd : EntityActionPlaySound
        { }

        [System.Serializable]
        public class EntityEventOnClick : EntitySerializedMethod
        { }
        #endregion

        #region Animations
        [System.Serializable]
        public class EntityActionAnimatorTrigger : EntitySerializedMethod
        {
            public string triggerName;
        }

        [System.Serializable]
        public class EntityActionAnimatorSetParameter : EntitySerializedMethod
        {
            public string parameterName;
            public string parameterValue;
            public string parameterType; //float, bool, int
        }
        #endregion

        #region Attention & Motion
        [System.Serializable]
        public class EntityActionLookAtTarget : EntitySerializedMethod
        {
            public string targetName;
            public float? duration;
        }

        [System.Serializable]
        public class EntityActionLookAtClear : EntitySerializedMethod
        {
        }
        [System.Serializable]
        public class EntityActionMoveToTarget : EntitySerializedMethod
        {
            public string targetName;
        }

        [System.Serializable]
        public class EntityActionMoveClear : EntitySerializedMethod
        {
        }
        #endregion
        #endregion

        #region Canvas Management
        [System.Serializable]
        public class NativeCanvasMouseOverEvent : SerializedMethod
        {
            public bool isOver;
        }
        #endregion

        #region Game Management
        [System.Serializable]
        public class GameActionSceneLoad : SerializedMethod
        {
            public string sceneName;
        }
        #endregion

        #region Spoon Brain
        [System.Serializable]
        public class SpoonBrainSetDomain : SerializedMethod
        {
            public string domainBaseUrl;
        }
        [System.Serializable]
        public class SpoonBrainGenerationVisual2D : SerializedMethod
        {
            public string description;
        }
        public class SpoonBrainVisual2DEventOnUrlAvailable : SpoonBrainGenerationVisual2D
        {
            public string url;
        }
        #endregion
    }
    #endregion
    #region Logic and converters
    public class FloatConverter : JsonConverter<float?>
    {
        public override float? ReadJson(JsonReader reader, System.Type objectType, float? existingValue, bool hasExistingValue, JsonSerializer serializer)
        {
            if (reader.TokenType == JsonToken.Null)
            {
                return null;
            }
            else
            {
                return System.Convert.ToSingle(reader.Value);
            }
        }

        public override void WriteJson(JsonWriter writer, float? value, JsonSerializer serializer)
        {
            if (value.HasValue)
            {
                writer.WriteValue(value.Value);
            }
            else
            {
                writer.WriteNull();
            }
        }
    }
    public class IntConverter : JsonConverter<int?>
    {
        public override int? ReadJson(JsonReader reader, System.Type objectType, int? existingValue, bool hasExistingValue, JsonSerializer serializer)
        {
            if (reader.TokenType == JsonToken.Null)
            {
                return null;
            }
            else
            {
                return System.Convert.ToInt32(reader.Value);
            }
        }

        public override void WriteJson(JsonWriter writer, int? value, JsonSerializer serializer)
        {
            if (value.HasValue)
            {
                writer.WriteValue(value.Value);
            }
            else
            {
                writer.WriteNull();
            }
        }
    }
    public class Vector3Converter : JsonConverter<Vector3?>
    {
        public override Vector3? ReadJson(JsonReader reader, System.Type objectType, Vector3? existingValue, bool hasExistingValue, JsonSerializer serializer)
        {
            if (reader.TokenType == JsonToken.Null)
            {
                return null;
            }
            else
            {
                var jsonObject = JObject.Load(reader);
                float x = jsonObject.GetValue("x").Value<float>();
                float y = jsonObject.GetValue("y").Value<float>();
                float z = jsonObject.GetValue("z").Value<float>();
                return new Vector3(x, y, z);
            }
        }

        public override void WriteJson(JsonWriter writer, Vector3? value, JsonSerializer serializer)
        {
            if (value.HasValue)
            {
                writer.WriteStartObject();
                writer.WritePropertyName("x");
                writer.WriteValue(value.Value.x);
                writer.WritePropertyName("y");
                writer.WriteValue(value.Value.y);
                writer.WritePropertyName("z");
                writer.WriteValue(value.Value.z);
                writer.WriteEndObject();
            }
            else
            {
                writer.WriteNull();
            }
        }
    }

    [Button]
    public void CallSerializedMethod(string serialized)
    {
        //Logger.Log("NativeBridge", $"CallSerializedMethod: {serialized}", Logger.Level.Debug);
        var serMethBase = JsonUtility.FromJson<SerializedMethod>(serialized);
        var method = this.GetType().GetMethod(serMethBase.methodName);
        var serMethChildType = method.GetParameters()[0].ParameterType;
        var genericMethod = typeof(JsonConvert).GetMethod("DeserializeObject", 1, new[] { typeof(string) }).MakeGenericMethod(serMethChildType);
        var serMethChild = genericMethod.Invoke(null, new object[] { serialized });
        method.Invoke(this, new object[] { serMethChild });
    }
    #endregion
    #endregion

    #region World (Create, Read, Update, Delete entities)
    private World m_world;

    [Button]
    public void WorldActionClear(SDK.WorldActionClear _data)
    {
        m_world.Clear();
    }


    [Button]
    public void WorldActionCreateOrUpdateEntity(WorldActionCreateOrUpdateEntity data)
    {
        m_world.CreateOrUpdateEntity(data.entityData);
    }
    #endregion

    #region Entities Actions: Audio
    SpoonBrain m_spoonBrain;

    [Button]
    public void EntityActionSay(EntityActionSay _data)
    {
        var audioSource = m_world.GetEntityByName(_data.entityName)?.GetComponentInChildren<AudioSource>();
        if (audioSource == null)
        {
            Logger.Log("[NativeBridge]", $"Entity {_data.entityName} does not have an audio source component.", Logger.Level.Warning);
        }
        m_spoonBrain.TTS(
            audioSource, 
            _data.text, 
            _data.voice, 
            _data.language,
            () =>
            {
                SendSerializedEvent(SerializedMethod.CreateDerived<SDK.EntityEventSayOnStart>(_data));
            },
            () =>
            {
                SendSerializedEvent(SerializedMethod.CreateDerived<SDK.EntityEventSayOnEnd>(_data));
            }
        );
    }

    [Button]
    public void EntityActionPlaySound(EntityActionPlaySound _data)
    {
        var audioSource = m_world.GetEntityByName(_data.entityName)?.GetComponentInChildren<AudioSource>();
        if (audioSource == null)
        {
            Logger.Log("[NativeBridge]", $"Entity {_data.entityName} does not have an audio source component.", Logger.Level.Warning);
        }
        StartCoroutine(AudioPlayer.PlayAudio(
            audioSource,
            _data.soundUrl,
            () =>
            {
                SendSerializedEvent(SerializedMethod.CreateDerived<SDK.EntityEventPlaySoundOnStart>(_data));
            },
            () =>
            {
                SendSerializedEvent(SerializedMethod.CreateDerived<SDK.EntityEventPlaySoundOnEnd>(_data));
            }
        ));
    }
    #endregion

    #region Entities Actions: Animation (Read / Update animator parameters for entities)

    [Button]
    public void EntityActionAnimatorTrigger(SDK.EntityActionAnimatorTrigger _data)
    {
        m_world.GetEntityByName(_data.entityName)?.GetComponentInChildren<Animator>().SetTrigger(_data.triggerName);
    }

    [Button]
    public void EntityActionAnimatorSetParameter(SDK.EntityActionAnimatorSetParameter _data)
    {
        if (_data.parameterType == "float")
        {
            m_world.GetEntityByName(_data.entityName)?.GetComponentInChildren<Animator>().SetFloat(_data.parameterName, float.Parse(_data.parameterValue));
        }
        else if (_data.parameterType == "bool")
        {
            m_world.GetEntityByName(_data.entityName)?.GetComponentInChildren<Animator>().SetBool(_data.parameterName, bool.Parse(_data.parameterValue));
        }
        else if (_data.parameterType == "int")
        {
            m_world.GetEntityByName(_data.entityName)?.GetComponentInChildren<Animator>().SetInteger(_data.parameterName, int.Parse(_data.parameterValue));
        }
    }

    [Button]
    public void EntityActionLookAtTarget(SDK.EntityActionLookAtTarget _data)
    {
        var ctrl = m_world.GetEntityByName(_data.entityName).GetComponentInChildren<GazeController>();
        if (ctrl == null)
        {
            Logger.Log("NativeBridge", $"Entity {_data.entityName} does not have a gaze controller", Logger.Level.Error);
            return;
        }
        var lookAtTarget = m_world.GetEntityByName(_data.targetName);
        ctrl.LockTarget(lookAtTarget.transform);
    }

    [Button]
    public void EntityActionLookAtClear(SDK.EntityActionLookAtClear _data)
    {
        var ctrl = m_world.GetEntityByName(_data.entityName).GetComponentInChildren<GazeController>();
        if (ctrl == null)
        {
            Logger.Log("NativeBridge", $"Entity {_data.entityName} does not have a gaze controller", Logger.Level.Error);
            return;
        }
        ctrl.ClearTarget();
    }
    [Button]
    public void EntityActionMoveToTarget(SDK.EntityActionMoveToTarget _data)
    {
        var ctrl = m_world.GetEntityByName(_data.entityName).GetComponentInChildren<MotionController>();
        if (ctrl == null)
        {
            Logger.Log("NativeBridge", $"Entity {_data.entityName} does not have a motion controller", Logger.Level.Error);
            return;
        }
        var target = m_world.GetEntityByName(_data.targetName);
        ctrl.SetTarget(target.transform);
    }

    [Button]
    public void EntityActionMoveClear(SDK.EntityActionMoveClear _data)
    {
        var ctrl = m_world.GetEntityByName(_data.entityName).GetComponentInChildren<MotionController>();
        if (ctrl == null)
        {
            Logger.Log("NativeBridge", $"Entity {_data.entityName} does not have a motion controller", Logger.Level.Error);
            return;
        }
        ctrl.ClearTarget();
    }
    #endregion

    #region Canvas Logic (Related to management of the Unity Canvas in the Native environment)

    private CanvasInputManager m_canvasInputManager;
    public void NativeCanvasMouseOverEvent(SDK.NativeCanvasMouseOverEvent data)
    {
        m_canvasInputManager.HandleMouseOverEvent(data.isOver);
    }
    #endregion

    #region GameState Manager (e.g. scenes)

    [Button]
    public void GameActionSceneLoad(SDK.GameActionSceneLoad data)
    {
        SceneManager.LoadScene(data.sceneName);
    }
    #endregion

    #region Spoon Brain
    [Button]
    public void SpoonBrainSetDomain(SDK.SpoonBrainSetDomain data)
    {
        m_spoonBrain.spoonBrainUrl = data.domainBaseUrl;
    }
    [Button]
    public void SpoonBrainGenerationVisual2D(SDK.SpoonBrainGenerationVisual2D data)
    {
        m_spoonBrain.GenerateVisual2D(data.description, (url) =>
        {
            var evt = SerializedMethod.CreateDerived<SpoonBrainVisual2DEventOnUrlAvailable>(data);
            evt.url = url;
            SendSerializedEvent(evt);
        });
    }
    #endregion
}
