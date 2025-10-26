# notif_listener.py
"""
仅供测试
TEST ONLY DO NOT APPLY FOR YOUR CLASSROOM!
WinRT-based Notification Listener (polling + XML parsing)
- Requires: pip install winrt
- Grant permission: Settings -> Privacy -> Notifications -> User notification access
- Run: python notif_listener.py
"""

import asyncio
import xml.etree.ElementTree as ET
from typing import List, Dict, Callable, Optional

# WinRT imports
from winrt.windows.ui.notifications.management import UserNotificationListener, UserNotificationListenerAccessStatus
from winrt.windows.ui.notifications import NotificationKinds

# --- Helper: parse toast xml (ToastGeneric) ---
def parse_toast_xml(xml_str: str) -> Dict:
    """
    Parse toast XML string and extract title, body (joined), image srcs (list), raw_xml.
    Returns dict with keys: title, body, images, raw_xml
    """
    result = {"title": "", "body": "", "images": [], "raw_xml": xml_str}
    if not xml_str:
        return result
    try:
        root = ET.fromstring(xml_str)
    except ET.ParseError:
        # not well-formed — return raw only
        return result

    # Find binding with template containing 'ToastGeneric' (case-insensitive)
    binding = None
    for b in root.findall(".//binding"):
        tmpl = b.attrib.get("template", "") or b.attrib.get("{http://www.w3.org/2000/xmlns/}template", "")
        if "toastgeneric" in tmpl.lower() or "generic" in tmpl.lower():
            binding = b
            break
    if binding is None:
        # fallback: first binding
        binding = root.find(".//binding") or root

    # collect <text> nodes — first one considered title
    texts = [t.text.strip() if t.text else "" for t in binding.findall(".//text") if (t.text and t.text.strip())]
    if texts:
        result["title"] = texts[0]
        if len(texts) > 1:
            result["body"] = "\n".join(texts[1:])
        else:
            result["body"] = ""
    # collect images
    images = []
    for img in binding.findall(".//image"):
        src = img.attrib.get("src") or img.attrib.get("placement") or ""
        if src:
            images.append(src)
    result["images"] = images
    return result

# --- Listener class (polling + diff) ---
class WinNotificationMonitor:
    def __init__(self, poll_interval: float = 1.0):
        self.listener = UserNotificationListener.get_current()
        self.poll_interval = poll_interval
        # store seen notification ids -> metadata
        self._seen = {}
        # user-supplied callback when new notification arrives
        self.on_new_notification: Optional[Callable[[dict], None]] = None

    async def ensure_access(self) -> bool:
        access = await self.listener.request_access_async()
        if access == UserNotificationListenerAccessStatus.ALLOWED:
            return True
        return False

    async def list_current(self):
        # fetch toast notifications
        notifs = await self.listener.get_notifications_async(NotificationKinds.TOAST)
        results = []
        for n in notifs:
            try:
                nid = n.id  # notification id (int)
            except Exception:
                nid = None
            # app info: try to get friendly name else fallback to id
            app_name = "<unknown app>"
            try:
                app_info = n.app_info
                if app_info:
                    try:
                        # Prefer AppInfo.DisplayInfo.DisplayName if available
                        display = app_info.display_info
                        if display:
                            app_name = display.display_name or app_info.id or app_name
                        else:
                            app_name = getattr(app_info, "id", app_name)
                    except Exception:
                        app_name = getattr(app_info, "id", app_name)
            except Exception:
                app_name = "<no-appinfo>"

            # time created (may be unavailable in some contexts)
            time_stamp = None
            try:
                time_stamp = n.notification.timestamp  # may raise/ be missing
            except Exception:
                time_stamp = None

            # notification XML string
            raw_xml = ""
            try:
                xml_obj = n.notification.get_xml()
                raw_xml = xml_obj.get_xml() if xml_obj else ""
            except Exception:
                raw_xml = ""

            parsed = parse_toast_xml(raw_xml)
            entry = {
                "id": nid,
                "app_name": app_name,
                "timestamp": str(time_stamp) if time_stamp is not None else None,
                "title": parsed["title"],
                "body": parsed["body"],
                "images": parsed["images"],
                "raw_xml": parsed["raw_xml"],
            }
            results.append(entry)
        return results

    async def run(self):
        ok = await self.ensure_access()
        if not ok:
            print("Access to UserNotificationListener denied. Please enable 'User notification access' in Settings -> Privacy -> Notifications.")
            return

        print("Notification monitor started. Poll interval:", self.poll_interval, "s")
        try:
            while True:
                current = await self.list_current()
                # build map id->entry; some notifications may have None id => use index fallback
                cur_map = {}
                for i, e in enumerate(current):
                    key = e["id"] if e["id"] is not None else f"__idx_{i}"
                    cur_map[key] = e

                # detect new ones
                for key, e in cur_map.items():
                    if key not in self._seen:
                        self._seen[key] = e
                        self._emit_new(e)
                # detect removed ones -> drop from _seen to avoid memory growth
                removed = [k for k in self._seen.keys() if k not in cur_map]
                for k in removed:
                    del self._seen[k]

                await asyncio.sleep(self.poll_interval)
        except asyncio.CancelledError:
            print("Monitor cancelled.")
        except KeyboardInterrupt:
            print("Interrupted by user; exiting.")

    def _emit_new(self, entry: dict):
        # print simple output
        print("=== New notification detected ===")
        print("From:", entry.get("app_name"))
        if entry.get("title"):
            print("Title:", entry["title"])
        if entry.get("body"):
            print("Body:", entry["body"])
        if entry.get("images"):
            print("Images:", ", ".join(entry["images"]))
        print("raw_xml (truncated):", (entry.get("raw_xml") or "")[:200])
        print("-------------------------------")
        # call user callback if set
        if self.on_new_notification:
            try:
                self.on_new_notification(entry)
            except Exception as ex:
                print("on_new_notification callback raised:", ex)

# --- Example usage ---
async def main():
    monitor = WinNotificationMonitor(poll_interval=1.0)

    # Example callback: do something with the new notification
    def my_callback(entry):
        # quick example: if it's from "WeChat" do something special
        app = (entry.get("app_name") or "").lower()
        if "QQ" in app or "腾讯" in app:
            print("[callback] QQ notification caught. Title:", entry.get("title"))

    monitor.on_new_notification = my_callback

    await monitor.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print("Fatal error:", e)
