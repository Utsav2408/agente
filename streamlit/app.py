from dotenv import load_dotenv
import streamlit as st
import requests
from datetime import datetime
from streamlit_cookies_manager import EncryptedCookieManager
import streamlit.components.v1 as components
import os
import html

load_dotenv()

# Load cookie secret
COOKIE_SECRET = os.getenv("COOKIE_KEY")
# Initialize cookie manager
cookies = EncryptedCookieManager(prefix="", password=COOKIE_SECRET)
if not cookies.ready():
    st.stop()

CREW_API_URL    = "http://localhost:8001"
BACKEND_API_URL = "http://localhost:8002"

# ─── Helpers ───────────────────────────────────────────────────────────────────

def handle_unauthorized():
    """
    Clear session and cookie on 403/expired token, then rerun to show login.
    """
    for key in [
        "logged_in", "user_id", "user_role", "user_name",
        "chat_history", "available_subjects", "grade", "session_token", "user_email",
    ]:
        st.session_state.pop(key, None)
    if "session_token" in cookies:
        del cookies["session_token"]
        cookies.save()
    st.error("Session expired or unauthorized. Please log in again.")
    st.rerun()

def _parse_iso(dt_str: str):
    """Safely parse ISO-like strings (supports 'Z')."""
    if not dt_str:
        return None
    try:
        return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    except Exception:
        return None

# ─── Restore Full Conversation ─────────────────────────────────────────────────

def restore_conversation():
    token = cookies.get("session_token")
    if not token:
        return False

    st.session_state["session_token"] = token
    headers = {"Authorization": f"Bearer {token}"}

    # Validate token
    try:
        resp = requests.get(f"{BACKEND_API_URL}/validate-token", headers=headers)
        validated_data = resp.json()
        if resp.status_code == 403 or not validated_data.get("valid", False):
            handle_unauthorized()
            return False
    except requests.exceptions.RequestException:
        st.error("Failed to validate session token.")
        return False

    # Fetch stored memory
    try:
        mem = requests.get(f"{BACKEND_API_URL}/session/memory", headers=headers)
        if mem.status_code == 403:
            handle_unauthorized()
            return False
        mem.raise_for_status()
        conversation_data = mem.json()
    except requests.exceptions.RequestException:
        st.error("Failed to restore session memory.")
        return False

    # Rehydrate chat_history
    chat = []
    for turn in conversation_data.get("conversation", []):
        try:
            ts = datetime.fromisoformat(turn["timestamp"]).strftime("%H:%M")
        except ValueError:
            ts = datetime.now().strftime("%H:%M")
        chat.append((turn["sender"], turn["message"], ts))
    if not chat:
        chat = [("bot", "👋 Welcome back!", datetime.now().strftime("%H:%M"))]

    # Update base session state
    st.session_state.update({
        "logged_in": True,
        "user_id": validated_data.get("user_id"),
        "user_role": validated_data.get("user_role"),
        "chat_history": chat
    })

    # Fetch missing profile info if needed
    if not all(k in st.session_state for k in ["user_name", "available_subjects", "grade", "user_email"]):
        profile = fetch_user_profile(
            st.session_state["user_id"],
            st.session_state["user_role"]
        )
        if profile:
            name = (
                f"{profile['first_name']} {profile['last_name']}"
                if st.session_state["user_role"] == "student"
                else profile.get('instructor_name', '')
            )
            st.session_state.update({
                "user_name": name,
                "available_subjects": profile.get("course_names", []),
                "grade": profile.get("grade") if st.session_state["user_role"] == "student" else None,
                "user_email": profile.get("instructor_email_id", "") if st.session_state["user_role"] == "teacher" else None,
            })

    return True

# ─── Authentication & Session ───────────────────────────────────────────────────

def verify_user(user_id, password):
    try:
        resp = requests.post(
            f"{BACKEND_API_URL}/verify",
            json={"user_id": user_id, "password": password}
        )
        resp.raise_for_status()
        data = resp.json()
        token = data.get("session_token")
        if token:
            st.session_state["session_token"] = token
            cookies["session_token"] = token
            cookies.save()
        return data
    except requests.exceptions.RequestException:
        st.error("Login failed. Please check your credentials.")
        return None

# ─── Fetch Profile ──────────────────────────────────────────────────────────────

def fetch_user_profile(user_id, user_role):
    try:
        headers = {}
        token = st.session_state.get("session_token")
        if token:
            headers["Authorization"] = f"Bearer {token}"
        url = (
            f"{BACKEND_API_URL}/student/{user_id}"
            if user_role == "student"
            else f"{BACKEND_API_URL}/instructor/{user_id}"
        )
        resp = requests.get(url, headers=headers)
        if resp.status_code == 403:
            handle_unauthorized()
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.RequestException:
        st.error("Failed to fetch user profile.")
        return None

# ─── Send Query ─────────────────────────────────────────────────────────────────

def send_query_to_backend(user_id, user_role, user_text, user_subjects=[], user_grade='', user_email=''):
    try:
        endpoint = f"{CREW_API_URL}/{user_role}/query"
        payload = {}
        if user_role == "student":
            payload.update({"query": user_text, "id": user_id, "grade": user_grade, "available_subjects": user_subjects})
        else:
            payload.update({"query": user_text, "instructor_id": user_id, "instructor_email": user_email, "available_subjects": user_subjects})
        headers = {}
        token = st.session_state.get("session_token")
        if token:
            headers["Authorization"] = f"Bearer {token}"
        resp = requests.post(endpoint, json=payload, headers=headers)
        if resp.status_code == 403:
            handle_unauthorized()
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.RequestException:
        st.error("⚠️ Failed to connect to backend.")
        return None

# ─── Announcements fetch (server-side fallback / not used by live widget) ──────

def fetch_announcements_for_grade(grade: str):
    """
    Kept for any server-side need; the live notifications use a client-side widget.
    """
    if not grade:
        return []
    try:
        headers = {}
        token = st.session_state.get("session_token")
        if token:
            headers["Authorization"] = f"Bearer {token}"
        resp = requests.get(f"{BACKEND_API_URL}/announcement/{grade}", headers=headers, timeout=10)
        if resp.status_code == 403:
            handle_unauthorized()
        resp.raise_for_status()
        data = resp.json()
        if not isinstance(data, list):
            return []
        data.sort(
            key=lambda a: (_parse_iso(a.get("posting_date")) or _parse_iso(a.get("event_date")) or datetime.min),
            reverse=True
        )
        return data
    except requests.exceptions.RequestException:
        return []

# ─── Sidebar: Enrolled/Assigned subjects as pretty badges ───────────────────────

def render_subject_badges(subjects):
    """
    Render subjects as non-clickable colored 'buttons' (badges).
    """
    if not subjects:
        return
    # A small pleasant palette
    palette = [
        "#E3F2FD", "#E8F5E9", "#FFF3E0", "#F3E5F5", "#E0F7FA",
        "#FCE4EC", "#FFFDE7", "#EDE7F6", "#E0F2F1", "#F1F8E9"
    ]
    text_palette = [
        "#0D47A1", "#1B5E20", "#E65100", "#4A148C", "#006064",
        "#880E4F", "#F57F17", "#311B92", "#004D40", "#33691E"
    ]
    badges = []
    for i, s in enumerate(subjects):
        bg = palette[i % len(palette)]
        fg = text_palette[i % len(text_palette)]
        label = html.escape(str(s))
        badges.append(
            f"<span style='display:inline-block;margin:4px 6px 0 0;padding:6px 10px;"
            f"border-radius:999px;background:{bg};color:{fg};font-size:0.85rem;"
            f"border:1px solid rgba(0,0,0,0.05);cursor:default;'>{label}</span>"
        )
    st.markdown("<div style='margin:4px 0 8px 0;'>" + "".join(badges) + "</div>", unsafe_allow_html=True)


def render_chat_bubble(sender: str, msg: str, ts: str, idx: int, clamp_chars: int = 180):
    """
    JS-free, iframe-free inline 'see more / see less' using a hidden checkbox + labels.
    Works inside st.markdown, keeps the toggle inline with the bot's sentence, and the
    bubble expands in the page (no inner scrolling).
    """
    base_style_user = "background:#e0f7fa;text-align:right;"
    base_style_bot  = "background:#f1f8e9;text-align:left;"
    time_div = f'<div style="font-size:0.7em;color:#888;">{ts}</div>'

    # Escape + preserve newlines
    safe_full_html = html.escape(str(msg)).replace("\n", "<br>")

    # USER (or short bot) → normal bubble
    if sender != "bot":
        st.markdown(
            f"<div style='{base_style_user if sender=='user' else base_style_bot} "
            f"padding:10px;border-radius:10px;margin:10px 0;'>"
            f"<strong>{sender.title()}:</strong> {safe_full_html}{time_div}</div>",
            unsafe_allow_html=True
        )
        return

    # BOT → build clamp + CSS toggle
    plain = html.unescape(safe_full_html.replace("<br>", "\n"))
    if len(plain) > clamp_chars:
        cut = plain[:clamp_chars]
        last_space = cut.rfind(" ")
        cut = cut if last_space == -1 else cut[:last_space]
        short_html = html.escape(cut).replace("\n", "<br>") + "… "
        needs_toggle = True
    else:
        short_html = safe_full_html
        needs_toggle = False

    style = base_style_bot
    if not needs_toggle:
        st.markdown(
            f"<div style='{style} padding:10px;border-radius:10px;margin:10px 0;'>"
            f"<strong>{sender.title()}:</strong> {safe_full_html}{time_div}</div>",
            unsafe_allow_html=True
        )
        return

    # Unique ids to scope CSS
    toggle_id = f"seeMoreToggle-{idx}"
    scope_cls = f"bubble-scope-{idx}"

    bubble_html = f"""
    <style>
      /* Scope all rules to just this bubble */
      .{scope_cls} .see-toggle {{
        position: absolute; left: -9999px; width: 1px; height: 1px; overflow: hidden; /* visually hidden checkbox */
      }}
      .{scope_cls} summary {{ display:inline; }}
      .{scope_cls} .preview {{ display:inline; }}
      .{scope_cls} .full {{ display:none; }}
      .{scope_cls} .more {{ display:inline; text-decoration:underline; cursor:pointer; }}
      .{scope_cls} .less {{ display:none; text-decoration:underline; cursor:pointer; }}

      /* When checked, swap preview/full + link text */
      .{scope_cls} .see-toggle:checked ~ .preview {{ display:none; }}
      .{scope_cls} .see-toggle:checked ~ .full {{ display:inline; }}
      .{scope_cls} .see-toggle:checked ~ .links .more {{ display:none; }}
      .{scope_cls} .see-toggle:checked ~ .links .less {{ display:inline; }}
    </style>

    <div class="{scope_cls}" style="{style} padding:10px;border-radius:10px;margin:10px 0;">
      <strong>{sender.title()}:</strong>
      <!-- Hidden checkbox controls the CSS state -->
      <input type="checkbox" id="{toggle_id}" class="see-toggle" />
      <span class="preview">{short_html}</span>
      <span class="full">{safe_full_html}</span>
      <span class="links">
        <label for="{toggle_id}" class="more">see more</label>
        <label for="{toggle_id}" class="less">see less</label>
      </span>
      {time_div}
    </div>
    """
    st.markdown(bubble_html, unsafe_allow_html=True)


# ─── Sidebar: Live Notifications (client-side fetch, no page reloads) ──────────

def render_notifications_sidebar_widget():
    """
    Renders a self-updating notifications stack **without reruns or page reloads**
    using a tiny HTML+JS widget (components.html). The widget:
      - polls GET /announcement/{grade} every 60s,
      - sends Authorization header with session token,
      - updates DOM only when data changes (shallow hash compare),
      - shows posting date (no hr:min),
      - no read/unread logic.
    """
    user_role = st.session_state.get("user_role", "")
    grade = st.session_state.get("grade")
    if user_role != "student":
        # Allow teacher to browse any grade
        grade = st.selectbox(
            "Select grade",
            options=[str(i) for i in range(1, 13)],
            index=9,
            key="notif_grade_select"
        )

    token = st.session_state.get("session_token", "")

    # Build a tiny HTML widget with client-side fetch & re-render
    # NOTE: Requires CORS to allow requests from the app origin to BACKEND_API_URL
    component_css = """
      <style>
        .notif-wrap { margin-top: 8px; }
        .notif-header { display:flex; align-items:center; gap:8px; font-weight:700; font-size:1.05rem; }
        .notif-card { margin-top:10px; padding:12px; border-radius:12px; background:#F6F6F6; border:1px solid #EEE; }
        .notif-meta { display:flex; justify-content:space-between; align-items:center; }
        .notif-title { font-weight:700; }
        .notif-date { font-size:0.8rem; color:#666; }
        .notif-content { font-size:0.9rem; margin:6px 0; }
        .notif-footer { display:flex; gap:12px; font-size:0.8rem; color:#444; }
        .notif-controls { margin-top:8px; }
        .notif-refresh-btn {
            width:100%; padding:8px 10px; border-radius:10px; border:1px solid #E0E0E0;
            background:#fff; cursor:pointer; font-weight:600;
        }
        .notif-refresh-btn:hover { background:#FAFAFA; }
        .notif-banner { margin-top:6px; padding:6px 10px; border-radius:8px; background:#EEF7FF; border:1px solid #CFE4FF; font-size:0.85rem; }
        .empty { margin-top:6px; color:#666; font-size:0.9rem; }
      </style>
    """

    # Escape for safe embedding
    safe_backend = html.escape(BACKEND_API_URL, quote=True)
    safe_grade   = html.escape(str(grade) if grade is not None else "", quote=True)
    safe_token   = html.escape(str(token), quote=True)

    component_html = f"""
      {component_css}
      <div class="notif-wrap" id="notif-wrap">
        <div class="notif-header">🔔 <span>Notifications</span></div>
        <div class="notif-controls">
          <button class="notif-refresh-btn" id="notif-refresh">↻ Refresh announcements</button>
        </div>
        <div id="notif-banner" style="display:none;" class="notif-banner">🆕 New announcement(s) fetched.</div>
        <div id="notif-list"></div>
        <div id="notif-empty" class="empty" style="display:none;">No announcements yet.</div>
      </div>

      <script>
        (function () {{
          const API_BASE = "{safe_backend}";
          const GRADE    = "{safe_grade}";
          const TOKEN    = "{safe_token}";
          const LIST     = document.getElementById("notif-list");
          const EMPTY    = document.getElementById("notif-empty");
          const BANNER   = document.getElementById("notif-banner");
          const REFRESH  = document.getElementById("notif-refresh");

          // Utility: shallow deterministic hash
          function hashData(arr) {{
            try {{
              // Sort by posting_date desc (fallback event_date), then stringify
              const sorted = [...arr].sort((a, b) => {{
                const pa = Date.parse(a.posting_date || a.event_date || 0) || 0;
                const pb = Date.parse(b.posting_date || b.event_date || 0) || 0;
                return pb - pa;
              }});
              return JSON.stringify(sorted);
            }} catch (e) {{
              return "";
            }}
          }}

          let lastHash = "";

          function formatDateOnly(iso) {{
            if (!iso) return "—";
            const d = new Date(iso);
            // Month short, day 2-digit, year numeric
            return d.toLocaleDateString(undefined, {{
              year: 'numeric', month: 'short', day: '2-digit'
            }});
          }}

          function cardHTML(a) {{
            const title   = a.title || "Untitled";
            const content = a.content || "";
            const poster  = a.poster_email || "unknown";
            const eventD  = formatDateOnly(a.event_date);
            const postD   = formatDateOnly(a.posting_date);

            return `
              <div class="notif-card">
                <div class="notif-meta">
                  <div class="notif-title">${{title}}</div>
                  <div class="notif-date">${{postD}}</div>
                </div>
                <div class="notif-content">${{content}}</div>
                <div class="notif-footer">
                  <span>🗓️ Event: <strong>${{eventD}}</strong></span>
                  <span>👤 ${{poster}}</span>
                </div>
              </div>
            `;
          }}

          function render(list) {{
            if (!Array.isArray(list) || list.length === 0) {{
              LIST.innerHTML = "";
              EMPTY.style.display = "block";
              return;
            }}
            EMPTY.style.display = "none";
            // sort newest first
            list.sort((a, b) => {{
              const pa = Date.parse(a.posting_date || a.event_date || 0) || 0;
              const pb = Date.parse(b.posting_date || b.event_date || 0) || 0;
              return pb - pa;
            }});
            LIST.innerHTML = list.map(cardHTML).join("");
          }}

          async function fetchAnnouncements(showBannerOnChange=true) {{
            if (!GRADE) {{
              render([]);
              return;
            }}
            try {{
              const resp = await fetch(`${{API_BASE}}/announcement/${{GRADE}}`, {{
                headers: TOKEN ? {{ "Authorization": "Bearer " + TOKEN }} : {{}}
              }});
              if (!resp.ok) throw new Error("HTTP " + resp.status);
              const data = await resp.json();
              if (!Array.isArray(data)) {{
                render([]);
                return;
              }}
              const newHash = hashData(data);
              if (newHash !== lastHash) {{
                render(data);
                if (showBannerOnChange) {{
                  BANNER.style.display = "block";
                  setTimeout(() => BANNER.style.display = "none", 2500);
                }}
                lastHash = newHash;
              }}
            }} catch (e) {{
              // Silently ignore; keep last rendered state
              console.error("Announcements fetch failed:", e);
            }}
          }}

          // Manual refresh button
          REFRESH.addEventListener("click", () => fetchAnnouncements(true));

          // Initial fetch & interval polling (60s)
          fetchAnnouncements(false);
          setInterval(fetchAnnouncements, 60000);
        }})();
      </script>
    """

    # Render the component. Height can be adjusted; set scrolling=True for long lists.
    components.html(component_html, height=600, scrolling=True)

# ─── Logout ─────────────────────────────────────────────────────────────────────

def logout():
    for key in [
        "logged_in", "user_id", "user_role", "user_name",
        "chat_history", "available_subjects", "grade", "session_token", "user_email",
    ]:
        st.session_state.pop(key, None)
    if "session_token" in cookies:
        del cookies["session_token"]
        cookies.save()
    st.rerun()

# ─── UI Screens ─────────────────────────────────────────────────────────────────

def show_login():
    st.title("🔐 Login")
    user_id  = st.text_input("User ID")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        user_data = verify_user(user_id, password)
        if user_data and user_data.get("verified"):
            profile = fetch_user_profile(user_data["user_id"], user_data["user_role"])
            if profile:
                name = (
                    f"{profile['first_name']} {profile['last_name']}"
                    if user_data["user_role"] == "student"
                    else profile.get('instructor_name','')
                )
                st.session_state.update({
                    "logged_in": True,
                    "user_id": user_data["user_id"],
                    "user_role": user_data["user_role"],
                    "user_name": name,
                    "available_subjects": profile.get("course_names",[]),
                    "grade": profile.get("grade") if user_data["user_role"] == "student" else None,
                    "user_email": profile.get("instructor_email_id", "") if user_data["user_role"] == "teacher" else None,
                    "chat_history": [("bot", f"👋 Welcome {name}! How can I assist you today?", datetime.now().strftime("%H:%M"))]
                })
                st.rerun()

def show_chat():
    st.title("💬 AgentE: Chat Assistant")

    with st.sidebar:
        # 🚪 Logout at the very top
        if st.button("🚪 Logout", use_container_width=True):
            logout()

        # Role and details (no "Logged in as")
        st.markdown(f"**Role:** `{st.session_state['user_role']}`")

        if st.session_state['user_role'] == 'student':
            grade = st.session_state.get('grade')
            if grade:
                st.markdown(f"**Grade:** `{grade}`")
            subs = st.session_state.get('available_subjects', [])
            if subs:
                st.markdown("**Enrolled Subjects:**")
                render_subject_badges(subs)  # ← pretty, non-clickable badges
        else:
            st.markdown(f"**Email:** `{st.session_state.get('user_email')}`")
            subs = st.session_state.get('available_subjects', [])
            if subs:
                st.markdown("**Assigned Subjects:**")
                render_subject_badges(subs)

        st.markdown("---")

        # 🔔 Live Notifications widget appears below the Logout & details
        render_notifications_sidebar_widget()

    # Initialize pending flag
    if 'pending' not in st.session_state:
        st.session_state['pending'] = False

    # Display chat history
    for i, (sender, msg, ts) in enumerate(st.session_state['chat_history']):
        render_chat_bubble(sender, msg, ts, idx=i, clamp_chars=500)

    # Chat input and message handling
    if not st.session_state['pending']:
        user_input = st.chat_input("Type your message...")
        if user_input:
            ts = datetime.now().strftime("%H:%M")
            st.session_state['chat_history'].append(('user', user_input, ts))
            st.session_state['last_user_input'] = user_input
            st.session_state['pending'] = True
            st.rerun()
    else:
        with st.spinner("🤖 Thinking..."):
            resp = send_query_to_backend(
                st.session_state['user_id'],
                st.session_state['user_role'],
                st.session_state.get('last_user_input', ''),
                st.session_state.get('available_subjects', []),
                str(st.session_state.get('grade', '')),
                st.session_state.get('user_email', '')
            )
        if resp is not None:
            reply = resp.get('response', str(resp)) if isinstance(resp, dict) else str(resp)
            st.session_state['chat_history'].append(('bot', reply, datetime.now().strftime("%H:%M")))
        st.session_state['pending'] = False
        st.rerun()

# ─── Main ───────────────────────────────────────────────────────────────────────

def main():
    st.set_page_config(page_title="Chat App", layout="wide")  # wide → sidebar more prominent
    if not st.session_state.get("logged_in", False):
        if not restore_conversation():
            show_login()
        else:
            show_chat()
    else:
        show_chat()

if __name__ == "__main__":
    main()
