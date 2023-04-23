mergeInto(LibraryManager.library, {

  NativeSendSerializedEvent: function (eventName, eventData) {
    const strEvtName = UTF8ToString(eventName)
    const strEvtData = UTF8ToString(eventData)
    const serializedEvent = new CustomEvent(strEvtName, {
        detail: {
            data: strEvtData
        }
    });
    window.dispatchEvent(serializedEvent);
  }
});