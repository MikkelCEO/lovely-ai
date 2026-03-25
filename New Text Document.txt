import { Device } from "@twilio/voice-sdk";

let device;
const CALL = "+4915888654546";

async function init() {
  try {
    const res = await fetch("http://localhost:5000/token");
    const data = await res.json();

    device = new Device(data.token, {
      logLevel: 1,
    });

    device.on("registered", () => {
      console.log("REGISTERED");
      document.getElementById("callBtn").disabled = false;
    });

    device.on("error", (error) => {
      console.error("TWILIO ERROR:", error);
    });

    await device.register();
  } catch (e) {
    console.error("INIT ERROR:", e);
  }
}

document.getElementById("callBtn").onclick = async () => {
  try {
    console.log("CALLING...");
    await device.connect({
      params: { To: CALL },
    });
  } catch (e) {
    console.error("CALL ERROR:", e);
  }
};

init();