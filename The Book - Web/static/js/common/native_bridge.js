import { post_to_authenticated_route } from './firebase.js';

//TODO Maybe there is a way to autogenerate this file from the C# code
export class NativeBridge {
    
    constructor(unityInstance) {
        this.unityInstance = unityInstance;

        //get the environment variable DEPLOYMENT 
        this.spoon_brain_url = "https://spoon-brain.dev.spoon-cloud.com";
        if (window.deployment === 'dev') {
            this.spoon_brain_url = "https://spoon-brain-staging.dev.spoon-cloud.com";
        }
        this.set_spoon_brain_url(this.spoon_brain_url);
    }

    callSeralizedMethod(serMeth) {
        //console.log(`Sending serialized method to Unity: ${serMeth}`);
        this.unityInstance.SendMessage('NativeBridge', 'CallSerializedMethod', serMeth);
    }

    set_spoon_brain_url(url) {
        const serMeth = JSON.stringify({
            methodName: "SpoonBrainSetDomain",
            spoonBrainUrl: url,
        });
        this.callSeralizedMethod(serMeth);
    }

    world_CreateOrUpdateEntity(entityName, prefabName = null, entityType = "ThreeD", position = null, scale = null, rotation = null, meshUrl = null, textureUrl = null) {
        const serMeth = JSON.stringify({
            methodName: "WorldActionCreateOrUpdateEntity",
            entityData: {
                name: entityName,
                prefabName: prefabName,
                entityType: entityType,
                position: position,
                scale: scale,
                rotation: rotation,
                meshUrl: meshUrl,
                textureUrl: textureUrl,
                width: null,
                height: null,
            }
        });
        this.callSeralizedMethod(serMeth);
    }

    entity_Animator_Set_Parameter(entityName, parameterName, parameterValue, parameterType="float") {
        const serMeth = JSON.stringify({
            methodName: "EntityActionAnimatorSetParameter",
            entityName: entityName,
            parameterName: parameterName,
            parameterValue: parameterValue,
            parameterType: parameterType
        });
        this.callSeralizedMethod(serMeth);
    }

    entity_Animator_Trigger(entityName, triggerName) {
        const serMeth = JSON.stringify({
            methodName: "EntityActionAnimatorTrigger",
            entityName: entityName,
            triggerName: triggerName
        });
        this.callSeralizedMethod(serMeth);
    }

    //Duration of -1.0 means infinite
    entity_LookAt_Target(agentName, targetName, duration = -1.0) {
        const serMeth = JSON.stringify({
            methodName: "EntityActionLookAtTarget",
            entityName: agentName,
            targetName: targetName,
            duration: duration,
        });
        this.callSeralizedMethod(serMeth);
    }
    
    //Release the constraint on looking at a target
    entity_LookAt_Clear(agentName) {
        const serMeth = JSON.stringify({
            methodName: "EntityActionLookAtClear",
            entityName: agentName,
        });
        this.callSeralizedMethod(serMeth);
    }

    entity_MoveTo_Target(agentName, targetName, duration = -1.0) {
        const serMeth = JSON.stringify({
            methodName: "EntityActionMoveToTarget",
            entityName: agentName,
            targetName: targetName,
            duration: duration,
        });
        this.callSeralizedMethod(serMeth);
    }
    
    entity_Move_Clear(agentName) {
        const serMeth = JSON.stringify({
            methodName: "EntityActionMoveClear",
            entityName: agentName,
        });
        this.callSeralizedMethod(serMeth);
    }

    async entity_Say(entityName, textToSay, voice = "jaina", language = "en") {
        //const serMeth = JSON.stringify({
        //    methodName: "EntityActionSay",
        //    entityName: entityName,
        //    text: textToSay,
        //    voice: voice,
        //    language: language,
        //});
        //this.callSeralizedMethod(serMeth);
               
        return new Promise(async (resolve, reject) => {
            const response = await post_to_authenticated_route(`/api/say`, { 'text': textToSay, 'voice': voice, 'language': language });
            if (response.ok) {
                const data = await response.json();
                console.log("Server response:", data);
                this.entity_Play_Sound("Myline", data.url);
                resolve(data.url);
            } else {
                console.error("Error:", response.statusText);
                reject(response.statusText);
            }
        });
    }

    entity_Play_Sound(entityName, soundUrl) {
        const serMeth = JSON.stringify({
            methodName: "EntityActionPlaySound",
            entityName: entityName,
            soundUrl: soundUrl,
        });
        this.callSeralizedMethod(serMeth);
    }

    scene_Load(sceneName) {
        const serMeth = JSON.stringify({
            methodName: "GameActionSceneLoad",
            sceneName: sceneName,
        });
        this.callSeralizedMethod(serMeth);
    }

    //This method also exists in the C# code, but getting back the url is cumbersome
    //better to use the JS version here.
    async generation_Visual_2D(promptText) {
        return new Promise((resolve, reject) => {
            var encodedPrompt = encodeURIComponent(`${promptText}`);
            const url = `${this.spoon_brain_url}/generation/visual/2D?user_input=${encodedPrompt}`;
            var myHeaders = new Headers();
            myHeaders.append("accept", "application/json");
            var requestOptions = {
                method: 'POST',
                headers: myHeaders,
                redirect: 'follow',
            };

            fetch(url, requestOptions)
            .then(response => response.json())
            .then(data => {
                resolve(data);
            })
            .catch(error => {
                reject(`Operation failed: ${error}`);
            }); 
        });
    }
    
    //TODO move the prompts methods to C# code
    async entity_Hear_And_Answer(entityName, promptText, userID) {       
        function removeBrackets(str) {
            return str.replace(/^\[(.*)\]$/, '$1');
        }

        return new Promise((resolve, reject) => {
            const url = `${this.spoon_brain_url}/characters/chat`;
            var raw = JSON.stringify({
                "character_name": entityName,
                "user_input": promptText,
                "user_id": userID
            });
            var myHeaders = new Headers();
            myHeaders.append("accept", "application/json");
            myHeaders.append("Content-Type", "application/json");

            var requestOptions = {
            method: 'POST',
            headers: myHeaders,
            body: raw,
            redirect: 'follow'
            };

            fetch(url, requestOptions)
            .then(response => response.json())
            .then(data => {
                const mirokaAnswer = data;// removeBrackets(data["spoon"]["text"]);
                console.log(`${entityName} answers ${mirokaAnswer}`);
                this.entity_Animator_Set_Parameter(entityName, "Emotional State", 1, "int");
                this.entity_Say(entityName, mirokaAnswer);
                resolve(mirokaAnswer);
            })
            .catch(error => {
                reject(`Operation failed: ${error}`);
            }); 
        });
    }
    
    async generation_Text_From_Prompt(promptId, params = {}) {       
        return new Promise((resolve, reject) => {
            const character_prompt_url = `${this.spoon_brain_url}/prompts/generate`;
            const bodyDef = JSON.stringify({
                "prompt_id": promptId,
                "parameters": params
            });
            var charPromptHeaders = new Headers();
            charPromptHeaders.append("accept", "application/json");
            charPromptHeaders.append("Content-Type", "application/json");
            const promptRequestOptions = {
                method: 'POST',
                headers: charPromptHeaders,
                body: bodyDef,
                redirect: 'follow'
            };
            fetch(character_prompt_url, promptRequestOptions)
                .then(response => response.json())
                .then(data => {
                    resolve(data);
                })
                .catch(error => {
                    reject(`Operation failed: ${error}`);
                });
        });
    }

    async entity_Set_Conversation_History(entityName, userId, conversationHistory = []) {       
        return new Promise((resolve, reject) => {
            const character_prompt_url = `${this.spoon_brain_url}/characters_v2/conversation/set_history`;
            const bodyDef = JSON.stringify({
                "character_name": entityName,
                "user_id": userId,
                "conversation_history": conversationHistory
            });
            var charPromptHeaders = new Headers();
            charPromptHeaders.append("accept", "application/json");
            charPromptHeaders.append("Content-Type", "application/json");
            const promptRequestOptions = {
                method: 'POST',
                headers: charPromptHeaders,
                body: bodyDef,
                redirect: 'follow'
            };
            fetch(character_prompt_url, promptRequestOptions)
                .then(response => response.json())
                .then(data => {
                    resolve(data);
                })
                .catch(error => {
                    reject(`Operation failed: ${error}`);
                });
        });
    }
}