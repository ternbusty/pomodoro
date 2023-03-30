import * as dt from "./utils/datetime.js";
import * as tb from "./utils/table.js";

let server_address = "http://192.168.11.11:8080";
// let server_address = "http://192.168.11.6:8080";

window.restore = document.getElementById("restore");
window.restart = document.getElementById("restart");
window.switch_button = document.getElementById("switch_mode_button");
window.take_long_break_button = document.getElementById(
  "take_long_break_button"
);
window.task_input = document.getElementById("task_input");
window.history_table = document.getElementById("history_table");
window.summary_table = document.getElementById("summary_table");
window.summarize_button = document.getElementById("summarize_button");
window.timer_status = "break";

// Prepare timers
window.work_timer = document.work_timer;
window.break_timer = document.break_timer;
window.total_working_timer = document.total_working_timer;
window.long_break_timer = document.long_break_timer;

// Setup worker to each timer
window.work_timer.worker = new Worker("./js/worker.js");
window.work_timer.worker.onmessage = function (e) {
  cntDown(window.work_timer);
};
window.break_timer.worker = new Worker("./js/worker.js");
window.break_timer.worker.onmessage = function (e) {
  cntDown(window.break_timer);
};
window.total_working_timer.worker = new Worker("./js/worker.js");
window.total_working_timer.worker.onmessage = function (e) {
  cntUp(window.total_working_timer);
};
window.long_break_timer.worker = new Worker("./js/worker.js");
window.long_break_timer.worker.onmessage = function (e) {
  cntDown(window.long_break_timer);
};

window.sync = function () {
  console.log("sync");
  fetch(`${server_address}/status/`, {
    method: "GET",
  })
    .then((response) => response.json())
    .then((data) => {
      console.log(data);
      let backend_status = data["status"];
      // Update frontend depends on backend status
      if (backend_status !== "not_started" && backend_status !== "finished" && backend_status !== "pause") {
        // disable: restart button
        window.restart.disabled = true;
      } else {
        // not started or finished or pause
        // - enable: restart
        // - disable: task_input, switch_button, take_long_break, summarize_button
        window.restart.disabled = false;
        window.task_input.disabled = true;
        window.switch_button.disabled = true;
        window.take_long_break_button.disabled = true;
        window.summarize_button.disabled = true;
      }
      // Stop all timers
      window.work_timer.worker.postMessage(0);
      window.total_working_timer.worker.postMessage(0);
      window.break_timer.worker.postMessage(0);
      // Process depend on backend status
      switch (backend_status) {
        case "finished":
          if (window.timer_status !== "finished") summarize(true);
          break;
        case "work":
          break2Work(true);
          break;
        case "break":
          work2break(true);
          break;
        case "pause":
          resetAllElements();
          window.restart.disabled = false;
      }
      // Set taskname from backend
      let backend_taskname = data["task_name"];
      if (backend_taskname !== null) setTaskStr(backend_taskname);
      // Update timer status
      window.timer_status = backend_status;
      // Update timers
      dt.setTime(window.work_timer, data["timers"]["work_timer"]);
      dt.setTime(window.break_timer, data["timers"]["break_timer"]);
      dt.setTime(
        window.total_working_timer,
        data["timers"]["total_working_timer"]
      );
      // Update history
      restoreHistory();
      // Judge if long break timer can be enabled
      if (backend_status === "work" || backend_status === "break") {
        fetch(`${server_address}/can_take_long_break/`, {
          method: "GET",
        })
          .then((response) => response.json())
          .then((data) => {
            if (data) window.take_long_break_button.disabled = false;
            else window.take_long_break_button.disabled = true;
          });
      } else {
        window.take_long_break_button.disabled = true;
      }
    });
  // Update summary
  updateSummary();
};

function getTaskStr() {
  let task_value = window.task_input.value;
  if (task_value === "") return "working";
  return `"${window.task_input.value}"`;
}

function setTaskStr(task_name) {
  if (task_name[0] === '"') task_name = task_name.slice(1);
  if (task_name[task_name.length - 1] === '"')
    task_name = task_name.slice(0, -1);
  window.task_input.value = task_name;
}

function cntDown(timer) {
  let time = dt.calcTime(timer);
  processTime(timer, time - 1);
}

function cntUp(timer) {
  let time = dt.calcTime(timer);
  processTime(timer, time + 1);
}

function processTime(timer, time) {
  if (time === 0) {
    if (timer.name === "work_timer") {
      dt.setTime(window.break_timer, dt.calcTime(window.break_timer) + 300);
      dt.setTime(timer, 1500);
    } else if (timer.name === "break_timer") {
      dt.setTime(timer, time);
    } else if (timer.name === "long_break_timer") {
      dt.setTime(timer, 18000);
      timer.worker.postMessage(0);
      document.getElementById("take_long_break_button").disabled = false;
    }
  } else dt.setTime(timer, time);
}

function work2break(isCalledBackend = false, add = 0) {
  // If long break starts, add to break_timer
  let new_break_time = dt.calcTime(break_timer) + add;
  dt.setTime(window.break_timer, new_break_time);
  // If is called from frontend, Call backend process
  if (!isCalledBackend) {
    let url = `${server_address}/start_break/`;
    if (add !== 0) url += `?break_time=${add}`;
    fetch(url, {
      method: "PUT",
    });
  }
  // Switch mode
  window.timer_status = "break";
  // Start or stop timers
  // - start: break_timer
  // - stop: work timer and total working timer
  window.work_timer.worker.postMessage(0);
  window.total_working_timer.worker.postMessage(0);
  window.break_timer.worker.postMessage(1);
  // Update elements
  // - enable: switch_button, summarize_button, task_input
  window.task_input.disabled = false;
  window.task_input.style.background = "white";
  window.switch_button.disabled = false;
  window.switch_button.value = "Back to work";
  window.switch_button.style.background = "#caddfc";
  window.summarize_button.disabled = false;
}

function break2Work(isCalledBackend = false) {
  let task_str = getTaskStr();
  // If is called from frontend, Call backend process
  if (!isCalledBackend) {
    let url = `${server_address}/start_work/`;
    if (task_str !== "") url += `?task_name=${task_str}`;
    fetch(url, {
      method: "PUT",
    });
  }
  // Switch mode
  window.timer_status = "work";
  // If break timer is negative, add to work timer
  if (dt.calcTime(break_timer) < 0) {
    dt.setTime(work_timer, dt.calcTime(work_timer) - dt.calcTime(break_timer));
    dt.setTime(break_timer, 0);
  }
  // Start or stop timers
  // - start: work timer and total working timer
  // - stop: break_timer
  window.break_timer.worker.postMessage(0);
  window.work_timer.worker.postMessage(1);
  window.total_working_timer.worker.postMessage(1);
  // Update elements
  // - enable: switch_button, summarize_button
  // - disable: task_input
  window.switch_button.value = "Take a break";
  window.switch_button.style.background = "#ffc0b8";
  window.task_input.disabled = true;
  window.task_input.style.background = "#f0f0f0";
  window.switch_button.disabled = false;
  window.summarize_button.disabled = false;
}

function deleteRowsFromTable(tbody_id) {
  var node = document.getElementById(tbody_id);
  while (node.hasChildNodes()) {
    node.removeChild(node.lastChild);
  }
}

function restoreHistory() {
  deleteRowsFromTable("history_table_body");
  fetch(`${server_address}/history/`, {
    method: "GET",
  })
    .then((response) => response.json())
    .then((data) => {
      console.log(data);
      let rows = data.split("\n");
      for (let i = 0; i < rows.length; i++) {
        if (rows[i] === "") continue;
        let cells = rows[i].split("\t");
        tb.addRow(window.history_table, [cells[0], cells[1]]);
      }
    });
}

function updateSummary() {
  fetch(`${server_address}/summary/`, {
    method: "GET",
  })
    .then((response) => response.json())
    .then((data) => {
      if (data !== "") {
        deleteRowsFromTable("summary_table_tbody");
        console.log(data);
        let rows = data.split("\n");
        for (let i = 0; i < rows.length; i++) {
          if (rows[i] === "") continue;
          let cells = rows[i].split("\t");
          tb.addRow(window.summary_table, [
            cells[0],
            cells[1],
            cells[2],
            cells[3],
          ]);
        }
      }
    });
}

function resetAllElements() {
  // Delete History Table
  deleteRowsFromTable("history_table_body");
  deleteRowsFromTable("summary_table_tbody");
  // Delete summarize header
  let summary_header = document.getElementById("summary_header");
  summary_header.innerHTML = "";
  // document.getElementById("summary_table_wrapper").style.visibility = "none";
  window.task_input.value = "";
  // disable elements other than Restore button
  window.summarize_button.style.display = "inline";
  window.switch_button.value = "Start working";
  window.switch_button.style.background = "#ffc0b8";
  window.task_input.disabled = true;
  window.task_input.style.background = "#f0f0f0";
  window.switch_button.disabled = true;
  window.summarize_button.disabled = true;
}

window.start = function (isCalledBackend = false) {
  // If is called from frontend, call backend process
  resetAllElements();
  fetch(`${server_address}/start/`, {
    method: "PUT",
  })
    .then((response) => response.json())
    .then((data) => {
      // break has aleardy started above, so no need to call /start_break here
      work2break(true);
      // Update frontend
      window.restart.disabled = true;
      window.take_long_break_button.disabled = false;
    });
};

window.switchMode = function (isCalledBackend = false) {
  window.restart.disabled = true;
  if (window.timer_status == "work") {
    work2break(isCalledBackend);
  } else {
    break2Work(isCalledBackend);
  }
};

window.takeLongBreak = function () {
  window.restart.disabled = true;
  if (window.timer_status === "break") window.break_timer.worker.postMessage(0);
  work2break(false, 1800);
  window.take_long_break_button.disabled = true;
  window.long_break_timer.worker.postMessage(1);
};

window.summarize = function (isCalledBackend = false) {
  window.timer_status = "finished";
  // Call Backend
  if (!isCalledBackend) {
    fetch(`${server_address}/summarize/`, {
      method: "PUT",
    });
  }
  // Stop timers
  window.break_timer.worker.postMessage(0);
  window.work_timer.worker.postMessage(0);
  window.total_working_timer.worker.postMessage(0);
  window.long_break_timer.worker.postMessage(0);
  // Add summarize header
  let summary_header = document.getElementById("summary_header");
  summary_header.innerHTML = "<h2>Summary</h2>";
  document.getElementById("summary_table_wrapper").style.visibility = "visible";
  // Hide or disable elements
  window.summarize_button.style.display = "none";
  window.long_break_timer.disabled = true;
  window.switch_button.disabled = true;
  window.task_input.disabled = true;
  updateSummary();
};
