# Roh.OperatorStation

Local FastAPI cockpit shell for Roh Operator Station.

Launch:

```bash
python nspl.py web launch Roh.OperatorStation --host 127.0.0.1 --port 8780
```

The app is discovered from `Web/Roh/OperatorStation/web.json` and exposes
`create_app(context)`. It checks the repo root, Python runtime, SkillCLI,
registered RohTalk skills, local SpeechNote voice provider state, and the DST
RohBridge snapshot through existing SkillCLI seams.

Roh chat uses a persistent RohTalk conversation titled `Roh Operator Station`.
The app resolves the existing titled conversation through `RohTalk.list_conversations`
and sends turns through `RohTalk.start` or `RohTalk.chat` with the `dst_director`
toolkit.

Voice support uses local SpeechNote skills:

- `Voice.Speak` for TTS
- `Voice.Listen` for SpeechNote clipboard STT

`Voice.Listen` calls SpeechNote's `start-listening-clipboard` action and reads
the desktop clipboard through `wl-paste`, `xclip`, or `xsel`.

Routes:

- `/`: Roh Operator Station cockpit shell
- `/health`: small JSON health response
- `/api/status`: status payload used by the shell
- `/send`: POST a prompt to the persistent RohTalk conversation
- `/listen`: POST to fill the command text from `Voice.Listen`
- `/speak`: POST the latest Roh response to `Voice.Speak`

Deferred:

- browser/native microphone capture
- DST command execution buttons
