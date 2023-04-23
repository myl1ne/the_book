using UnityEngine;

public class CameraController : MonoBehaviour
{
    public Camera m_camera;
    public float m_movementSpeed = 10f;
    public float m_lookSpeed = 1000f;

    void Update()
    {
        if (Input.GetMouseButton(1))
        {
            float horizontal = Input.GetAxis("Horizontal");
            float vertical = Input.GetAxis("Vertical");
            float mouseX = Input.GetAxis("Mouse X");
            float mouseY = Input.GetAxis("Mouse Y");

            m_camera.transform.position += (m_camera.transform.forward * vertical + m_camera.transform.right * horizontal) * m_movementSpeed * Time.deltaTime;
            m_camera.transform.Rotate(Vector3.up * mouseX * m_lookSpeed * Time.deltaTime, Space.World);
            m_camera.transform.Rotate(Vector3.right * -mouseY * m_lookSpeed * Time.deltaTime, Space.Self);
        }
    }
}