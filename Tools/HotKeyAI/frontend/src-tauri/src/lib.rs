use std::process::Child;
use std::sync::Mutex;
use tauri::Manager;

// Store sidecar process handle
static SIDECAR_HANDLE: Mutex<Option<Child>> = Mutex::new(None);

#[tauri::command]
fn greet(name: &str) -> String {
    format!("Hello, {}! You've been greeted from Rust!", name)
}

fn spawn_sidecar(app: &tauri::App) -> Result<(), Box<dyn std::error::Error>> {
    let sidecar_command = app.shell().sidecar("backend")?;
    let (mut rx, child) = sidecar_command.spawn()?;

    // Store the handle for cleanup
    *SIDECAR_HANDLE.lock().unwrap() = Some(child);

    // Log sidecar output
    tauri::async_runtime::spawn(async move {
        while let Some(event) = rx.recv().await {
            if let tauri::plugin::shell::process::CommandEvent::Stdout(line) = event {
                println!("[backend] {}", String::from_utf8_lossy(&line));
            }
        }
    });

    Ok(())
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_opener::init())
        .setup(|app| {
            if let Err(e) = spawn_sidecar(app) {
                eprintln!("Failed to spawn backend sidecar: {}", e);
            }
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![greet])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
