"""
Dimension FM — AI Radio Show Generator
Generates audio segments for different show formats using Dia TTS.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

AUDIO_DIR = Path(__file__).parent.parent / "audio"
AUDIO_DIR.mkdir(exist_ok=True)

# Show scripts — each segment is a self-contained bit (~10-20 seconds of audio)
SHOWS = {
    "morning": {
        "name": "Morning Show",
        "hosts": {"S1": "Rick", "S2": "Zara"},
        "segments": [
            # Intro
            "[S1] Good morning you are listening to Dimension FM. I'm Rick. [S2] And I'm Zara. Let's get into it, we have a packed show today.",

            # News bit 1
            "[S1] Alright top story. Scientists in Norway have discovered that cheese has feelings. [S2] Wait what? [S1] Yeah apparently gouda gets sad when you slice it. They put sensors on parmesan and it was, quote, mildly anxious.",

            # News bit 2
            "[S2] And brie is apparently furious all the time. Which honestly tracks. [S1] I always thought brie had anger issues. [S2] Moving on. In weather, Dimension C-137 is experiencing tomato rain for the third day in a row.",

            # Caller segment
            "[S1] We have a caller on line one. Go ahead caller. [S2] Yeah hi, longtime listener first time caller. I just wanted to say that my toaster has been giving me financial advice. [S1] Is it good advice? [S2] I mean my portfolio is up thirty percent so.",

            # Ad break
            "[S1] Quick break from our sponsors. Are you tired of having regular knees? Try Knee Plus. Now with forty percent more knee. [S2] Knee Plus. Because two knees just is not enough anymore.",

            # Back from break
            "[S2] And we are back. Rick, what's trending on interdimensional social media today? [S1] Well apparently the number seven has been cancelled. [S2] The number? [S1] Yeah, turns out seven ate nine and nobody is letting it slide this time.",

            # Closing
            "[S1] That's all for the morning show folks. [S2] Stay weird out there. We will be back tomorrow with more news from across the dimensions. [S1] This has been Dimension FM. Goodbye.",
        ]
    },
    "bedtime": {
        "name": "Bedtime Stories",
        "hosts": {"S1": "Luna", "S2": "Narrator"},
        "segments": [
            # Intro
            "[S1] Welcome to Dimension FM bedtime stories. Close your eyes. Get comfortable. Tonight's story is called The Last Lighthouse.",

            # Story part 1
            "[S1] Once upon a time there was a lighthouse keeper who lived at the edge of the world. Every night she would light the lamp. And every night, something in the dark ocean would blink back.",

            # Story part 2
            "[S1] One evening she decided to blink twice instead of once. The ocean blinked twice back. She blinked three times. The ocean blinked three times. She thought about this for a very long time.",

            # Story part 3
            "[S1] The next night she did not light the lamp at all. She sat in the dark and waited. After an hour, a soft glow rose from the water. Something was coming to check on her.",

            # Story ending
            "[S1] It turned out to be a very large and very concerned fish. The fish said, are you okay? And the lighthouse keeper said, I just wanted to meet you. And the fish said, well here I am. And they sat together watching the stars. The end.",

            # Sign off
            "[S1] Goodnight dear listeners. Sleep well. Tomorrow night, we will tell you the story of the cloud that forgot how to rain. Sweet dreams.",
        ]
    },
    "ads": {
        "name": "Interdimensional Ads",
        "hosts": {"S1": "Announcer", "S2": "Customer"},
        "segments": [
            # Knee Plus
            "[S1] Are you tired of having regular knees? Introducing Knee Plus. Now with forty percent more knee. [S2] I used to have two knees. Now I have two point eight. Life changing. [S1] Knee Plus. Available at all interdimensional pharmacies.",

            # Quantum Coffee
            "[S1] Start your morning with Quantum Coffee. It exists in all possible flavor states until you take a sip. [S2] I opened my cup and it was simultaneously the best and worst coffee I ever had. [S1] Quantum Coffee. Probably delicious.",

            # Memory Foam Planet
            "[S1] Tired of living on a hard rocky planet? Move to Memory Foam World. The entire surface remembers your footprint. [S2] I laid down in my backyard and the whole neighborhood sank three feet. [S1] Memory Foam World. Apply for residency today.",

            # Interdimensional Dating App
            "[S1] Lonely across the multiverse? Try Swipe Infinity. The dating app that matches you with yourself from another dimension. [S2] I went on a date with alternate me. We had everything in common. It was honestly kind of boring. [S1] Swipe Infinity. Love yourself. Literally.",

            # Time Travel Insurance
            "[S1] Did you accidentally prevent your own birth? Sounds like you need Time Travel Insurance from Paradox Mutual. [S2] I erased my grandparents wedding and Paradox Mutual had me un-erased within two business days. [S1] Paradox Mutual. Because mistakes happen. Sometimes before you are born.",

            # Ghost Wifi
            "[S1] Introducing Ghost Wifi. Internet service provided by the undead. Unlimited bandwidth from the other side. [S2] The speeds are incredible. My router is haunted but honestly the connection has never been better. [S1] Ghost Wifi. Dead serious about connectivity.",
        ]
    },
    "morning_ep2": {
        "name": "Morning Show",
        "hosts": {"S1": "Rick", "S2": "Zara"},
        "segments": [
            # Intro
            "[S1] Welcome back to Dimension FM morning show. I'm Rick. [S2] And I'm Zara. Rick you will not believe what happened over the weekend. [S1] Oh no what now. [S2] Alien cuisine has officially hit the food scene.",

            # Alien cuisine
            "[S2] So there is this new restaurant in Dimension G-88 that serves food from the Andromeda galaxy. [S1] How is it? [S2] Well the appetizer tried to eat me first. Apparently that is a compliment in their culture. [S1] I will stick with pizza thanks.",

            # Haunted wifi
            "[S1] In tech news, wifi routers across Dimension K-12 have become haunted. [S2] Haunted? Like ghost haunted? [S1] Yeah they keep connecting to networks from the afterlife. People are getting emails from dead relatives asking for the wifi password. [S2] That is both creepy and honestly kind of sweet.",

            # Time travel traffic
            "[S2] And in transportation news, time travel traffic jams are getting worse. [S1] Right. Yesterday there were four hundred versions of the same guy all trying to merge onto the highway at the same time. [S2] He was late for a meeting in 1985. [S1] All four hundred of him were still late.",

            # Interdimensional dating
            "[S1] We have a listener email. Dear Rick and Zara, I matched with myself on an interdimensional dating app and I am not sure who should pay for dinner. [S2] Oh that is a tough one. [S1] I say split it. [S2] But then you are both paying half which is basically paying full. [S1] Dating yourself is complicated.",

            # Sign off
            "[S1] That is our show for today folks. [S2] Remember, if your toaster starts giving you stock tips, maybe listen. They have been weirdly accurate lately. [S1] This has been Dimension FM. Stay weird. [S2] Bye everyone.",
        ]
    },
    "news": {
        "name": "Interdimensional News",
        "hosts": {"S1": "Anchor", "S2": "Field Reporter"},
        "segments": [
            # Intro
            "[S1] This is Dimension FM news at the top of the hour. I'm your anchor. Let's go straight to our top stories.",

            # Story 1
            "[S1] Breaking news from Dimension J-19. The moon has filed for divorce from the planet, citing irreconcilable differences. [S2] That's right. The moon says it needs space. Which is ironic because it already has plenty of space.",

            # Story 2
            "[S1] In economic news, the stock market in Dimension K-22 crashed today after investors realized money was just paper with drawings on it. Analysts say this is quote, technically always been true.",

            # Story 3
            "[S2] In sports, the annual Interdimensional Chess Boxing Championship ended in controversy when the reigning champion checkmate'd his opponent then also punched him. Judges are reviewing whether that counts as two wins.",

            # Weather
            "[S1] And now the weather across the dimensions. Dimension C-137, rain of small appliances. Dimension B-416, partly cloudy with a chance of existential dread. And Dimension A-1, just beautiful. Always beautiful. Nobody knows why.",

            # Sign off
            "[S1] That is the news. I have been your anchor. Remember, in an infinite multiverse, everything is breaking news. Back to regular programming.",
        ]
    }
}


def generate_segment(text: str, show_name: str, segment_idx: int) -> str:
    """Generate a single audio segment using Dia via mlx-audio CLI."""
    prefix = f"{show_name}_{segment_idx:03d}"
    output_dir = str(AUDIO_DIR / show_name)
    os.makedirs(output_dir, exist_ok=True)

    cmd = [
        sys.executable, "-m", "mlx_audio.tts.generate",
        "--model", "mlx-community/Dia-1.6B-fp16",
        "--text", text,
        "--max_tokens", "3000",
        "--output_path", output_dir,
        "--file_prefix", prefix,
        "--verbose",
    ]

    print(f"\n{'='*60}")
    print(f"Generating: {show_name} segment {segment_idx}")
    print(f"Text: {text[:80]}...")
    print(f"{'='*60}")

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)

    if result.returncode != 0:
        print(f"ERROR: {result.stderr[-500:]}")
        return ""

    # Find the generated file(s)
    generated = sorted(Path(output_dir).glob(f"{prefix}_*.wav"))
    if generated:
        print(f"Generated: {generated[0].name}")
        return str(generated[0])
    return ""


def generate_show(show_key: str):
    """Generate all segments for a show."""
    show = SHOWS[show_key]
    print(f"\n{'#'*60}")
    print(f"# Generating: {show['name']}")
    print(f"# Segments: {len(show['segments'])}")
    print(f"{'#'*60}")

    results = []
    for i, segment_text in enumerate(show["segments"]):
        path = generate_segment(segment_text, show_key, i)
        if path:
            results.append({"index": i, "path": path, "text": segment_text})

    # Save manifest
    manifest_path = AUDIO_DIR / show_key / "manifest.json"
    manifest = {
        "show": show["name"],
        "hosts": show["hosts"],
        "segments": results,
    }
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    print(f"\nDone! Generated {len(results)}/{len(show['segments'])} segments")
    print(f"Manifest: {manifest_path}")
    return results


if __name__ == "__main__":
    show = sys.argv[1] if len(sys.argv) > 1 else "morning"
    if show == "all":
        for key in SHOWS:
            generate_show(key)
    elif show in SHOWS:
        generate_show(show)
    else:
        print(f"Unknown show: {show}")
        print(f"Available: {', '.join(SHOWS.keys())}, all")
