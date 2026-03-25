import { Device } from "@twilio/voice-sdk";

let device;
const CALL = "+4915888654546";

const logBox = document.getElementById("log");

function log(text, type = "info") {
  const el = document.createElement("div");
  el.className = "entry " + type;
  el.textContent = text;
  logBox.appendChild(el);
  logBox.scrollTop = logBox.scrollHeight;
}

async function init() {
  try {
    log("Fetching token...");
    const res = await fetch("http://localhost:5000/token");
    const data = await res.json();

    device = new Device(data.token, { logLevel: 1 });

    device.on("registered", () => {
      log("Device ready", "ok");
      document.getElementById("callBtn").disabled = false;
    });

    device.on("error", (e) => log("Error: " + e.message, "err"));
    device.on("connect", () => log("Call connected", "ok"));
    device.on("disconnect", () => log("Call ended"));
    device.on("incoming", () => log("Incoming call"));

    await device.register();

  } catch (e) {
    log("Init failed: " + e.message, "err");
  }
}

document.getElementById("callBtn").onclick = async () => {
  try {
    log("Calling...");
    await device.connect({
      params: { To: CALL }
    });
  } catch (e) {
    log("Call failed: " + e.message, "err");
  }
};

init();