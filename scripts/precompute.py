#!/usr/bin/env python3
"""
Pre-compute all deployment data for Evoke.

Generates:
- worker/src/data/images.json   (image URLs + CLIP embeddings)
- worker/src/data/directions.json (mood direction vectors)
- worker/src/data/demo.json      (pre-computed demo results)

Usage:
    cd ml && uv run python ../scripts/precompute.py [--demo-audio path/to/audio.mp3]
"""

import argparse
import json
import sys
from io import BytesIO
from pathlib import Path

import numpy as np
import requests
from PIL import Image

# Add ml/ to path so we can import src.bridge and src.audio_encoder
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "ml"))

from src.audio_encoder import AudioEncoder
from src.bridge import CrossModalBridge

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "worker" / "src" / "data"

# Curated Unsplash images (~250 images organized by mood category)
SAMPLE_IMAGES = [
    # === HIGH ENERGY: concerts, lightning, fire, sports, waves crashing ===
    "https://images.unsplash.com/photo-1459749411175-04bf5292ceea?w=400",  # concert crowd
    "https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=400",  # concert lights
    "https://images.unsplash.com/photo-1492684223066-81342ee5ff30?w=400",  # festival
    "https://images.unsplash.com/photo-1516450360452-9312f5e86fc7?w=400",  # dance party
    "https://images.unsplash.com/photo-1429552077091-836152271555?w=400",  # lightning storm
    "https://images.unsplash.com/photo-1461511669078-d46bf351cd6e?w=400",  # lightning bolt
    "https://images.unsplash.com/photo-1532978379173-523e16f371f2?w=400",  # fire sparks
    "https://images.unsplash.com/photo-1549317661-bd32c8ce0afa?w=400",  # bonfire
    "https://images.unsplash.com/photo-1474552226712-ac0f0961a954?w=400",  # basketball action
    "https://images.unsplash.com/photo-1461896836934-bd45ba8920c7?w=400",  # surfing wave
    "https://images.unsplash.com/photo-1502680390548-bdbac40e4ce3?w=400",  # crashing wave
    "https://images.unsplash.com/photo-1519058082700-08a0b56da9b4?w=400",  # extreme sport
    "https://images.unsplash.com/photo-1504450758481-7338bbe75731?w=400",  # fireworks
    "https://images.unsplash.com/photo-1498931299476-f16f7ee5ed44?w=400",  # fireworks sky
    "https://images.unsplash.com/photo-1530549387789-4c1017266635?w=400",  # swimming race
    "https://images.unsplash.com/photo-1517649763962-0c623066013b?w=400",  # cycling race
    "https://images.unsplash.com/photo-1541534741688-6078c6bfb5c5?w=400",  # gym workout
    "https://images.unsplash.com/photo-1468413253725-0d5181091126?w=400",  # stormy ocean
    "https://images.unsplash.com/photo-1507272931001-fc06c17e4f43?w=400",  # rain storm
    "https://images.unsplash.com/photo-1527576539890-dfa815648363?w=400",  # explosive color
    "https://images.unsplash.com/photo-1551892374-ecf8754cf8b0?w=400",  # volcano
    "https://images.unsplash.com/photo-1486870591958-9b9d0d1dda99?w=400",  # mountain peak dramatic
    "https://images.unsplash.com/photo-1454789548928-9efd52dc4031?w=400",  # space earth
    "https://images.unsplash.com/photo-1446776811953-b23d57bd21aa?w=400",  # rocket launch
    "https://images.unsplash.com/photo-1535083783855-76ae62b2914e?w=400",  # neon lights

    # === LOW ENERGY: zen gardens, fog, snow, still water, soft light ===
    "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=400",  # portrait calm
    "https://images.unsplash.com/photo-1509316785289-025f5b846b35?w=400",  # still water
    "https://images.unsplash.com/photo-1439405326854-014607f694d7?w=400",  # calm ocean
    "https://images.unsplash.com/photo-1505144808419-1957a94ca61e?w=400",  # misty mountains
    "https://images.unsplash.com/photo-1488866022916-f7f2a032cd23?w=400",  # foggy scene
    "https://images.unsplash.com/photo-1478760329108-5c3ed9d495a0?w=400",  # dark minimal
    "https://images.unsplash.com/photo-1418985227306-7b2a91e2ced0?w=400",  # snow landscape
    "https://images.unsplash.com/photo-1491002052546-bf38f186af56?w=400",  # snowy mountain
    "https://images.unsplash.com/photo-1477601263568-180e2c6d046e?w=400",  # snow trees
    "https://images.unsplash.com/photo-1482192505345-5655af888cc4?w=400",  # fog forest
    "https://images.unsplash.com/photo-1485236715568-ddc5ee6ca227?w=400",  # soft morning light
    "https://images.unsplash.com/photo-1510414842594-a61c69b5ae57?w=400",  # calm beach
    "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=400",  # serene beach
    "https://images.unsplash.com/photo-1499209974431-9dddcece7f88?w=400",  # peaceful person
    "https://images.unsplash.com/photo-1506126613408-eca07ce68773?w=400",  # meditation
    "https://images.unsplash.com/photo-1528715471579-d1bcf0ba5e83?w=400",  # zen stones
    "https://images.unsplash.com/photo-1544367567-0f2fcb009e0b?w=400",  # yoga
    "https://images.unsplash.com/photo-1518241353330-0f7941c2d9b5?w=400",  # zen garden
    "https://images.unsplash.com/photo-1476673160081-cf065607f449?w=400",  # soft rain
    "https://images.unsplash.com/photo-1501426026826-31c667bdf23d?w=400",  # gentle sunlight
    "https://images.unsplash.com/photo-1414609245224-afa02bfb3fda?w=400",  # calm field
    "https://images.unsplash.com/photo-1431794062232-2a99a5431c6c?w=400",  # dreamy landscape
    "https://images.unsplash.com/photo-1470252649378-9c29740c9fa8?w=400",  # golden hour field
    "https://images.unsplash.com/photo-1500534314209-a25ddb2bd429?w=400",  # still lake
    "https://images.unsplash.com/photo-1509233725247-49e657c54213?w=400",  # peaceful coast

    # === HIGH VALENCE: sunsets, flowers, celebrations, colorful markets ===
    "https://images.unsplash.com/photo-1503803548695-c2a7b4a5b875?w=400",  # golden sunset
    "https://images.unsplash.com/photo-1476820865390-c52aeebb9891?w=400",  # warm sunset
    "https://images.unsplash.com/photo-1495616811223-4d98c6e9c869?w=400",  # vibrant sunset
    "https://images.unsplash.com/photo-1490682143684-14369e18dce8?w=400",  # warm landscape
    "https://images.unsplash.com/photo-1490750967868-88aa4f44baee?w=400",  # flowers field
    "https://images.unsplash.com/photo-1487530811176-3780de880c2d?w=400",  # cherry blossoms
    "https://images.unsplash.com/photo-1462275646964-a0e3c11f18a6?w=400",  # sunflowers
    "https://images.unsplash.com/photo-1455659817273-f96807779a8a?w=400",  # tulips colorful
    "https://images.unsplash.com/photo-1508610048659-a06b669e3321?w=400",  # flower close-up
    "https://images.unsplash.com/photo-1464457312035-3d7d0e0c058e?w=400",  # autumn warm
    "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=400",  # bright mountain
    "https://images.unsplash.com/photo-1475924156734-496f6cac6ec1?w=400",  # golden light nature
    "https://images.unsplash.com/photo-1469474968028-56623f02e42e?w=400",  # sunny landscape
    "https://images.unsplash.com/photo-1433086966358-54859d0ed716?w=400",  # waterfall
    "https://images.unsplash.com/photo-1504198453319-5ce911bafcde?w=400",  # bright nature
    "https://images.unsplash.com/photo-1465056836041-7f43ac27dcb5?w=400",  # bright valley
    "https://images.unsplash.com/photo-1472214103451-9374bd1c798e?w=400",  # sunny meadow
    "https://images.unsplash.com/photo-1518998053901-5348d3961a04?w=400",  # colorful paint
    "https://images.unsplash.com/photo-1525310512210-d8c1b5e42e0c?w=400",  # hot air balloons
    "https://images.unsplash.com/photo-1513151233558-d860c5398176?w=400",  # confetti celebration
    "https://images.unsplash.com/photo-1530103862676-de8c9debad1d?w=400",  # balloons party
    "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?w=400",  # majestic mountain
    "https://images.unsplash.com/photo-1426604966848-d7adac402bff?w=400",  # bright forest
    "https://images.unsplash.com/photo-1501854140801-50d01698950b?w=400",  # green hills
    "https://images.unsplash.com/photo-1470071459604-3b5ec3a7fe05?w=400",  # misty forest bright

    # === LOW VALENCE: rain, abandoned buildings, dark forests, moody ===
    "https://images.unsplash.com/photo-1534088568595-a066f410bcda?w=400",  # moody atmospheric
    "https://images.unsplash.com/photo-1507400492013-162706c8c05e?w=400",  # dark moody
    "https://images.unsplash.com/photo-1489549132488-d00b7eee80f1?w=400",  # night scene
    "https://images.unsplash.com/photo-1516912481808-3406841bd33c?w=400",  # dark clouds
    "https://images.unsplash.com/photo-1499346030926-9a72daac6c63?w=400",  # night sky dark
    "https://images.unsplash.com/photo-1515266591878-f93e32bc5937?w=400",  # dark forest
    "https://images.unsplash.com/photo-1473081556163-2a17de81fc97?w=400",  # foggy dark trees
    "https://images.unsplash.com/photo-1428908728789-d2de25dbd4e2?w=400",  # abandoned building
    "https://images.unsplash.com/photo-1518156677180-95a2893f3e9f?w=400",  # rainy window
    "https://images.unsplash.com/photo-1501691223387-dd0500403074?w=400",  # rainy street
    "https://images.unsplash.com/photo-1468276311594-df7cb65d8df6?w=400",  # dark mountains
    "https://images.unsplash.com/photo-1536431311719-398b6704d4cc?w=400",  # melancholic sky
    "https://images.unsplash.com/photo-1445251836269-d158eaa028a6?w=400",  # cold dark water
    "https://images.unsplash.com/photo-1508669232496-137b159c1cdb?w=400",  # dark cityscape
    "https://images.unsplash.com/photo-1494972308805-463bc619d34e?w=400",  # cold winter
    "https://images.unsplash.com/photo-1518241353330-0f7941c2d9b5?w=400",  # somber garden
    "https://images.unsplash.com/photo-1504608524841-42fe6f032b4b?w=400",  # grey sky
    "https://images.unsplash.com/photo-1485470733090-0aae1788d668?w=400",  # ruins
    "https://images.unsplash.com/photo-1531315630201-bb15abeb1653?w=400",  # cold blue
    "https://images.unsplash.com/photo-1494438639946-1ebd1d20bf85?w=400",  # cold minimal
    "https://images.unsplash.com/photo-1519681393784-d120267933ba?w=400",  # dark mountains star
    "https://images.unsplash.com/photo-1454496522488-7a8e488e8606?w=400",  # dramatic peak
    "https://images.unsplash.com/photo-1486728297118-82a07bc48a28?w=400",  # dark landscape
    "https://images.unsplash.com/photo-1493246507139-91e8fad9978e?w=400",  # moody lake
    "https://images.unsplash.com/photo-1518837695005-2083093ee35b?w=400",  # dark water

    # === HIGH TEMPO: racing, traffic, birds in flight, rushing water ===
    "https://images.unsplash.com/photo-1541185933-ef5d8ed016c2?w=400",  # race car
    "https://images.unsplash.com/photo-1449965408869-eaa3f722e40d?w=400",  # car driving fast
    "https://images.unsplash.com/photo-1494976388531-d1058494cdd8?w=400",  # sports car
    "https://images.unsplash.com/photo-1514539079130-25950c84af65?w=400",  # traffic motion
    "https://images.unsplash.com/photo-1476514525535-07fb3b4ae5f1?w=400",  # speedboat wake
    "https://images.unsplash.com/photo-1480936600919-bffa6b7ecf1e?w=400",  # rushing water
    "https://images.unsplash.com/photo-1433838552652-f9a46b332c40?w=400",  # birds flying
    "https://images.unsplash.com/photo-1444464666168-49d633b86797?w=400",  # bird in flight
    "https://images.unsplash.com/photo-1506012787146-f92b2d7d6d96?w=400",  # running person
    "https://images.unsplash.com/photo-1552674605-db6ffd4facb5?w=400",  # trail running
    "https://images.unsplash.com/photo-1473445730015-841f29a9490b?w=400",  # rushing river
    "https://images.unsplash.com/photo-1509023464722-18d996393ca8?w=400",  # blurred motion
    "https://images.unsplash.com/photo-1449824913935-59a10b8d2000?w=400",  # busy city
    "https://images.unsplash.com/photo-1480714378408-67cf0d13bc1b?w=400",  # city traffic
    "https://images.unsplash.com/photo-1477959858617-67f85cf4f1df?w=400",  # urban rush
    "https://images.unsplash.com/photo-1514565131-fce0801e5785?w=400",  # city lights motion
    "https://images.unsplash.com/photo-1444723121867-7a241cacace9?w=400",  # city night trails
    "https://images.unsplash.com/photo-1519501025264-65ba15a82390?w=400",  # city street motion
    "https://images.unsplash.com/photo-1534430480872-3498386e7856?w=400",  # horse galloping
    "https://images.unsplash.com/photo-1501785888041-af3ef285b470?w=400",  # fast landscape
    "https://images.unsplash.com/photo-1470770841497-7e0e6b9cbbe1?w=400",  # skateboarding
    "https://images.unsplash.com/photo-1558618666-fcd25c85f82e?w=400",  # dynamic texture
    "https://images.unsplash.com/photo-1553356084-58ef4a67b2a7?w=400",  # fluid motion paint
    "https://images.unsplash.com/photo-1541701494587-cb58502866ab?w=400",  # abstract flow
    "https://images.unsplash.com/photo-1550859492-d5da9d8e45f3?w=400",  # abstract energy

    # === LOW TEMPO: still life, meditation, empty rooms, quiet lakes ===
    "https://images.unsplash.com/photo-1497436072909-60f360e1d4b1?w=400",  # still forest
    "https://images.unsplash.com/photo-1508739773434-c26b3d09e071?w=400",  # still sunset
    "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?w=400",  # quiet forest
    "https://images.unsplash.com/photo-1415241497727-b8e12e726198?w=400",  # still lake reflection
    "https://images.unsplash.com/photo-1507692049790-de58290a4334?w=400",  # quiet wheat field
    "https://images.unsplash.com/photo-1508193638397-1c4234db14d8?w=400",  # autumn path still
    "https://images.unsplash.com/photo-1473773508845-188df20aaec4?w=400",  # empty road
    "https://images.unsplash.com/photo-1446776858070-70c3d5ed6758?w=400",  # moon still
    "https://images.unsplash.com/photo-1445964047600-cdbdb873673e?w=400",  # still pond
    "https://images.unsplash.com/photo-1510797215324-95aa89f43c33?w=400",  # quiet countryside
    "https://images.unsplash.com/photo-1476611338391-6f395a0ebc7b?w=400",  # still life fruit
    "https://images.unsplash.com/photo-1495195134817-aeb325a55b65?w=400",  # candle still life
    "https://images.unsplash.com/photo-1515377905703-c4788e51af15?w=400",  # tea cup still
    "https://images.unsplash.com/photo-1507608616759-54f48f0af0ee?w=400",  # empty dock
    "https://images.unsplash.com/photo-1509114397022-ed747cca3f65?w=400",  # quiet room
    "https://images.unsplash.com/photo-1519710164239-da123dc03ef4?w=400",  # minimal interior
    "https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?w=400",  # empty apartment
    "https://images.unsplash.com/photo-1494438639946-1ebd1d20bf85?w=400",  # cold stillness
    "https://images.unsplash.com/photo-1499002238440-d264edd596ec?w=400",  # still desk
    "https://images.unsplash.com/photo-1416339442236-8ceb164046f8?w=400",  # quiet vineyard
    "https://images.unsplash.com/photo-1439853949127-fa647821eba0?w=400",  # calm aerial
    "https://images.unsplash.com/photo-1434394354979-a235cd36269d?w=400",  # misty tree
    "https://images.unsplash.com/photo-1493552152660-f915ab47ae9d?w=400",  # quiet bridge
    "https://images.unsplash.com/photo-1506744038136-46273834b3fb?w=400",  # calm valley
    "https://images.unsplash.com/photo-1472396961693-142e6e269027?w=400",  # deer still

    # === HIGH TEXTURE: fractals, architecture detail, forests, machinery ===
    "https://images.unsplash.com/photo-1557672172-298e090bd0f1?w=400",  # abstract detail
    "https://images.unsplash.com/photo-1549490349-8643362247b5?w=400",  # fractal pattern
    "https://images.unsplash.com/photo-1543857778-c4a1a3e0b2eb?w=400",  # complex pattern
    "https://images.unsplash.com/photo-1550684848-fac1c5b4e853?w=400",  # texture detail
    "https://images.unsplash.com/photo-1557682250-33bd709cbe85?w=400",  # gradient complex
    "https://images.unsplash.com/photo-1557682224-5b8590cd9ec5?w=400",  # gradient layers
    "https://images.unsplash.com/photo-1518241353330-0f7941c2d9b5?w=400",  # garden detail
    "https://images.unsplash.com/photo-1470165301023-58dab8118cc9?w=400",  # coral reef
    "https://images.unsplash.com/photo-1509023464722-18d996393ca8?w=400",  # complex sky
    "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=400",  # clock mechanism
    "https://images.unsplash.com/photo-1504275107627-0c2ba7a43dba?w=400",  # leaf veins macro
    "https://images.unsplash.com/photo-1509228627152-72ae9ae6848d?w=400",  # wood grain
    "https://images.unsplash.com/photo-1506792006437-256b665541e2?w=400",  # butterfly wing
    "https://images.unsplash.com/photo-1519120944692-1a8d8cfc107f?w=400",  # dense forest canopy
    "https://images.unsplash.com/photo-1497366754035-f200968a6e72?w=400",  # modern architecture
    "https://images.unsplash.com/photo-1511818966892-d7d671e672a2?w=400",  # building geometry
    "https://images.unsplash.com/photo-1487958449943-2429e8be8625?w=400",  # architecture facade
    "https://images.unsplash.com/photo-1481277542470-605612bd2d61?w=400",  # ornate interior
    "https://images.unsplash.com/photo-1520355731687-a0da7ceb4123?w=400",  # stained glass
    "https://images.unsplash.com/photo-1485083269755-a7b559a4fe09?w=400",  # intricate nature
    "https://images.unsplash.com/photo-1473181488821-2d23949a045a?w=400",  # city detail
    "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=400",  # machinery detail
    "https://images.unsplash.com/photo-1505765050516-f72dcac9c60e?w=400",  # autumn leaves detail
    "https://images.unsplash.com/photo-1476673160081-cf065607f449?w=400",  # rain texture
    "https://images.unsplash.com/photo-1525338078858-d762b5e32f2c?w=400",  # marble texture

    # === LOW TEXTURE: minimal architecture, empty skies, desert, clean ===
    "https://images.unsplash.com/photo-1494438639946-1ebd1d20bf85?w=400",  # minimal surface
    "https://images.unsplash.com/photo-1478760329108-5c3ed9d495a0?w=400",  # dark minimal
    "https://images.unsplash.com/photo-1531315630201-bb15abeb1653?w=400",  # cold minimal
    "https://images.unsplash.com/photo-1509114397022-ed747cca3f65?w=400",  # clean room
    "https://images.unsplash.com/photo-1519710164239-da123dc03ef4?w=400",  # minimal decor
    "https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?w=400",  # simple interior
    "https://images.unsplash.com/photo-1508921340878-ba53e1f016ec?w=400",  # empty desert
    "https://images.unsplash.com/photo-1509316785289-025f5b846b35?w=400",  # clean horizon
    "https://images.unsplash.com/photo-1504608524841-42fe6f032b4b?w=400",  # empty sky
    "https://images.unsplash.com/photo-1468276311594-df7cb65d8df6?w=400",  # bare mountain
    "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=400",  # clean beach
    "https://images.unsplash.com/photo-1510414842594-a61c69b5ae57?w=400",  # simple coast
    "https://images.unsplash.com/photo-1505144808419-1957a94ca61e?w=400",  # minimal peak
    "https://images.unsplash.com/photo-1439405326854-014607f694d7?w=400",  # bare ocean
    "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=400",  # simple portrait
    "https://images.unsplash.com/photo-1506744038136-46273834b3fb?w=400",  # minimal valley
    "https://images.unsplash.com/photo-1500534314209-a25ddb2bd429?w=400",  # bare lake
    "https://images.unsplash.com/photo-1414609245224-afa02bfb3fda?w=400",  # open field
    "https://images.unsplash.com/photo-1431794062232-2a99a5431c6c?w=400",  # soft minimal
    "https://images.unsplash.com/photo-1488866022916-f7f2a032cd23?w=400",  # foggy minimal
    "https://images.unsplash.com/photo-1446776811953-b23d57bd21aa?w=400",  # space minimal
    "https://images.unsplash.com/photo-1446776858070-70c3d5ed6758?w=400",  # moon simple
    "https://images.unsplash.com/photo-1499346030926-9a72daac6c63?w=400",  # night minimal
    "https://images.unsplash.com/photo-1473773508845-188df20aaec4?w=400",  # empty road
    "https://images.unsplash.com/photo-1507608616759-54f48f0af0ee?w=400",  # empty pier

    # === GENERAL VARIETY: portraits, food, animals, space, underwater, art ===
    "https://images.unsplash.com/photo-1474511320723-9a56873867b5?w=400",  # fox wildlife
    "https://images.unsplash.com/photo-1437622368342-7a3d73a34c8f?w=400",  # turtle underwater
    "https://images.unsplash.com/photo-1504006833117-8886a355efbf?w=400",  # dog portrait
    "https://images.unsplash.com/photo-1495446815901-a7297e633e8d?w=400",  # books
    "https://images.unsplash.com/photo-1506744038136-46273834b3fb?w=400",  # yosemite valley
    "https://images.unsplash.com/photo-1472396961693-142e6e269027?w=400",  # deer nature
    "https://images.unsplash.com/photo-1462331940025-496dfbfc7564?w=400",  # nebula space
    "https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=400",  # earth from space
    "https://images.unsplash.com/photo-1419242902214-272b3f66ee7a?w=400",  # milky way
    "https://images.unsplash.com/photo-1444703686981-a3abbc4d4fe3?w=400",  # stars
    "https://images.unsplash.com/photo-1546026423-cc4642628d2b?w=400",  # jellyfish underwater
    "https://images.unsplash.com/photo-1544551763-46a013bb70d5?w=400",  # fish underwater
    "https://images.unsplash.com/photo-1559827291-bce5f6300b8d?w=400",  # coral underwater
    "https://images.unsplash.com/photo-1484723091739-30a097e8f929?w=400",  # food plating
    "https://images.unsplash.com/photo-1476224203421-9ac39bcb3327?w=400",  # food dish
    "https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=400",  # food overhead
    "https://images.unsplash.com/photo-1540189549336-e6e99c3679fe?w=400",  # food colorful
    "https://images.unsplash.com/photo-1551963831-b3b1ca40c98e?w=400",  # breakfast
    "https://images.unsplash.com/photo-1452457750107-cd084dce177d?w=400",  # cat portrait
    "https://images.unsplash.com/photo-1415369629372-26f2fe60c467?w=400",  # cat close
    "https://images.unsplash.com/photo-1543466835-00a7907e9de1?w=400",  # dog cute
    "https://images.unsplash.com/photo-1518020382113-a7e8fc38eac9?w=400",  # pug dog
    "https://images.unsplash.com/photo-1425082661507-6af0db88b66a?w=400",  # whale tail
    "https://images.unsplash.com/photo-1564349683136-77e08dba1ef7?w=400",  # giraffe
    "https://images.unsplash.com/photo-1456926631375-92c8ce872def?w=400",  # zebra
    "https://images.unsplash.com/photo-1534567153574-2b12153a87f0?w=400",  # parrot colorful
    "https://images.unsplash.com/photo-1507679799987-c73779587ccf?w=400",  # suited portrait
    "https://images.unsplash.com/photo-1531746020798-e6953c6e8e04?w=400",  # face portrait
    "https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?w=400",  # man portrait
    "https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=400",  # woman portrait
    "https://images.unsplash.com/photo-1517694712202-14dd9538aa97?w=400",  # laptop coding
    "https://images.unsplash.com/photo-1550745165-9bc0b252726f?w=400",  # retro gaming
    "https://images.unsplash.com/photo-1485827404703-89b55fcc595e?w=400",  # robot technology
    "https://images.unsplash.com/photo-1518770660439-4636190af475?w=400",  # circuit board
    "https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?w=400",  # matrix code
    "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?w=400",  # guitar music
    "https://images.unsplash.com/photo-1507838153414-b4b713384a76?w=400",  # piano music
    "https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f?w=400",  # singer stage
    "https://images.unsplash.com/photo-1470229722913-7c0e2dbbafd3?w=400",  # crowd concert
    "https://images.unsplash.com/photo-1511379938547-c1f69419868d?w=400",  # sheet music
    "https://images.unsplash.com/photo-1513364776144-60967b0f800f?w=400",  # paint brushes art
    "https://images.unsplash.com/photo-1460661419201-fd4cecdf8a8b?w=400",  # paint art
    "https://images.unsplash.com/photo-1547891654-e66ed7ebb968?w=400",  # abstract sculpture
    "https://images.unsplash.com/photo-1536924940846-227afb31e2a5?w=400",  # abstract art
    "https://images.unsplash.com/photo-1499781350541-7783f6c6a0c8?w=400",  # graffiti art
    "https://images.unsplash.com/photo-1507608616759-54f48f0af0ee?w=400",  # pier sunset
    "https://images.unsplash.com/photo-1520962922320-2038eebab146?w=400",  # tropical beach
    "https://images.unsplash.com/photo-1519046904884-53103b34b206?w=400",  # sunny beach
    "https://images.unsplash.com/photo-1505228395891-9a51e7e86bf6?w=400",  # palm trees
    "https://images.unsplash.com/photo-1501785888041-af3ef285b470?w=400",  # scenic vista
    "https://images.unsplash.com/photo-1470770841497-7e0e6b9cbbe1?w=400",  # skateboarding
    "https://images.unsplash.com/photo-1502680390548-bdbac40e4ce3?w=400",  # ocean power
    "https://images.unsplash.com/photo-1500622944204-b135684e99fd?w=400",  # sunset silhouette
    "https://images.unsplash.com/photo-1490730141103-6cac27aaab94?w=400",  # person sunset
    "https://images.unsplash.com/photo-1485470733090-0aae1788d668?w=400",  # old ruins
    "https://images.unsplash.com/photo-1473181488821-2d23949a045a?w=400",  # city rooftop
    "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?w=400",  # restaurant interior
    "https://images.unsplash.com/photo-1555396273-367ea4eb4db5?w=400",  # cafe interior
    "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=400",  # scenic mountain
    "https://images.unsplash.com/photo-1454496522488-7a8e488e8606?w=400",  # mountain drama
    "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?w=400",  # mountain range
    "https://images.unsplash.com/photo-1486728297118-82a07bc48a28?w=400",  # landscape wide
    "https://images.unsplash.com/photo-1475924156734-496f6cac6ec1?w=400",  # nature golden
    "https://images.unsplash.com/photo-1501854140801-50d01698950b?w=400",  # green nature
    "https://images.unsplash.com/photo-1469474968028-56623f02e42e?w=400",  # bright nature
    "https://images.unsplash.com/photo-1426604966848-d7adac402bff?w=400",  # forest light
    "https://images.unsplash.com/photo-1472214103451-9374bd1c798e?w=400",  # meadow
    "https://images.unsplash.com/photo-1465056836041-7f43ac27dcb5?w=400",  # valley view
    "https://images.unsplash.com/photo-1433086966358-54859d0ed716?w=400",  # waterfall scene
    "https://images.unsplash.com/photo-1504198453319-5ce911bafcde?w=400",  # nature color
    "https://images.unsplash.com/photo-1470252649378-9c29740c9fa8?w=400",  # golden field
    "https://images.unsplash.com/photo-1519681393784-d120267933ba?w=400",  # starry mountain
    "https://images.unsplash.com/photo-1493246507139-91e8fad9978e?w=400",  # lake scene
    "https://images.unsplash.com/photo-1518837695005-2083093ee35b?w=400",  # water scene
    "https://images.unsplash.com/photo-1470071459604-3b5ec3a7fe05?w=400",  # forest mist
    "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?w=400",  # green forest
]


def download_image(url: str) -> Image.Image:
    """Download an image from a URL."""
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return Image.open(BytesIO(response.content)).convert("RGB")


def compute_direction_vectors(bridge: CrossModalBridge) -> dict:
    """Compute semantic direction vectors using CLIP text embeddings via bridge."""
    print("Computing semantic direction vectors from CLIP...")
    directions = bridge.compute_direction_vectors()
    return {k: v.tolist() for k, v in directions.items()}


def l2_distance(a: np.ndarray, b: np.ndarray) -> float:
    """Compute L2 (Euclidean) distance between two vectors."""
    diff = a - b
    return float(np.sqrt(np.dot(diff, diff)))


def brute_force_search(
    query: np.ndarray,
    images: list[dict],
    top_k: int = 20,
) -> list[dict]:
    """Brute-force L2 search over image embeddings."""
    scored = []
    for i, img in enumerate(images):
        emb = np.array(img["embedding"], dtype=np.float32)
        dist = l2_distance(query, emb)
        scored.append({"id": i, "image_url": img["url"], "score": dist})

    scored.sort(key=lambda x: x["score"])
    return scored[:top_k]


def main():
    parser = argparse.ArgumentParser(description="Pre-compute Evoke deployment data")
    parser.add_argument(
        "--demo-audio",
        type=str,
        help="Path to demo audio file (mp3/wav). If provided, generates demo data and copies to frontend/public/demo.mp3",
    )
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("Loading CLIP model...")
    bridge = CrossModalBridge()
    bridge.load_model()
    print("CLIP model ready")

    # Deduplicate URLs while preserving order
    seen = set()
    unique_images = []
    for url in SAMPLE_IMAGES:
        if url not in seen:
            seen.add(url)
            unique_images.append(url)

    # Step 1: Compute image embeddings
    total = len(unique_images)
    print(f"\nProcessing {total} unique images...")
    image_entries = []
    failed = 0
    for i, url in enumerate(unique_images):
        print(f"  [{i + 1}/{total}] {url[:60]}...")
        try:
            image = download_image(url)
            embedding = bridge.encode_image(image)
            image_entries.append({
                "url": url,
                "embedding": embedding.tolist(),
            })
        except requests.RequestException as e:
            print(f"    Failed to download: {e}")
            failed += 1
        except Exception as e:
            print(f"    Failed to encode: {e}")
            failed += 1

    print(f"\nSuccessfully processed {len(image_entries)}/{total} images ({failed} failed)")

    # Write images.json
    images_path = OUTPUT_DIR / "images.json"
    with open(images_path, "w") as f:
        json.dump(image_entries, f)
    print(f"Wrote {images_path}")

    # Step 2: Compute semantic direction vectors
    directions = compute_direction_vectors(bridge)
    directions_path = OUTPUT_DIR / "directions.json"
    with open(directions_path, "w") as f:
        json.dump(directions, f)
    print(f"Wrote {directions_path}")

    # Step 3: Generate demo data (if audio provided)
    if args.demo_audio:
        print(f"\nProcessing demo audio: {args.demo_audio}")
        encoder = AudioEncoder()
        encoder.load_model()

        with open(args.demo_audio, "rb") as f:
            audio_data = f.read()

        embedding, mood = encoder.encode(audio_data, "auto")
        clip_embedding = bridge.project_to_clip_space(embedding)

        demo_images = brute_force_search(clip_embedding, image_entries, top_k=20)

        demo_data = {
            "embedding": clip_embedding.tolist(),
            "mood_energy": mood["energy"],
            "mood_valence": mood["valence"],
            "mood_tempo": mood["tempo"],
            "mood_texture": mood["texture"],
            "images": demo_images,
        }

        demo_path = OUTPUT_DIR / "demo.json"
        with open(demo_path, "w") as f:
            json.dump(demo_data, f)
        print(f"Wrote {demo_path}")

        # Copy audio to frontend/public/demo.mp3
        frontend_demo = Path(__file__).resolve().parent.parent / "frontend" / "public" / "demo.mp3"
        import shutil
        shutil.copy2(args.demo_audio, frontend_demo)
        print(f"Copied demo audio to {frontend_demo}")
    else:
        # Generate demo data without audio (use a synthetic embedding)
        print("\nNo demo audio provided, generating synthetic demo data...")
        # Use a random but deterministic embedding for the demo
        rng = np.random.RandomState(123)
        demo_embedding = rng.randn(512).astype(np.float32)
        norm = np.linalg.norm(demo_embedding)
        if norm > 0:
            demo_embedding = demo_embedding / norm

        demo_images = brute_force_search(demo_embedding, image_entries, top_k=20)

        demo_data = {
            "embedding": demo_embedding.tolist(),
            "mood_energy": 0.5,
            "mood_valence": 0.5,
            "mood_tempo": 0.5,
            "mood_texture": 0.5,
            "images": demo_images,
        }

        demo_path = OUTPUT_DIR / "demo.json"
        with open(demo_path, "w") as f:
            json.dump(demo_data, f)
        print(f"Wrote {demo_path}")

    print("\nPre-computation complete!")


if __name__ == "__main__":
    main()
