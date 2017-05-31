import logging

import aiohttp

logger = logging.getLogger(__name__)

SIEGE_APP_ID = '39baebad-39e5-4552-8c25-2c9b919064e2'
AUTH = SESSION = None

LOGIN_URL = 'https://uplayconnect.ubi.com/ubiservices/v2/profiles/sessions'

PLATFORMS = ['PC', 'PSN', 'XBL']

PLATFORM_URLS = {
    'PC': ('5172a557-50b5-4665-b7db-e3f2e8c5041d', 'OSBOR_PC_LNCH_A'),
    'PSN': ('05bfb3f7-6c21-4c42-be1f-97a33fb5cf66', 'OSBOR_PS4_LNCH_A'),
    'XBL': ('98a601e5-ca91-4440-b1c5-753f601a2c90', 'OSBOR_XBOXONE_LNCH_A'),
}

async def get_profiles(username: str = None, user_id: str = None):
    if user_id is None:
        url = 'https://api-ubiservices.ubi.com/v2/profiles'
    else:
        url = 'https://public-ubiservices.ubi.com/v2/users/{}/profiles'.format(user_id)
    params = {'nameOnPlatform': username, 'platformType': 'uplay'} if user_id is None else {}
    return await get_page(url, params)


async def get_page(url, params, result_type='json', do_login=True, headers = {}):
    if AUTH is None:
        await login()

    full_headers = {
        'User-Agent': 'AvaBot/1.0.0',
        'Ubi-AppId': SIEGE_APP_ID,
        'Authorization': AUTH,
        'ubi-sessionid': SESSION,
    }
    full_headers.update(headers)

    session = aiohttp.ClientSession(headers=full_headers)
    async with session.get(url, params=params) as req:
        logger.info("GET => {}".format(req.url))
        assert isinstance(req, aiohttp.ClientResponse)
        if req.status == 401 and do_login:
            await login()
            result = await get_page(url, params, result_type=result_type, do_login=False)
        elif req.status != 200:
            print(await req.read())
            result = None
        else:
            result = await getattr(req, result_type)()
    session.close()
    return result

async def login():
    global AUTH, SESSION

    headers = {
        "User-Agent": "AvaBot/1.0.0",
        'Ubi-RequestedPlatformType': 'uplay',
        'Ubi-AppId': SIEGE_APP_ID,
        'Authorization': 'Basic %s' % LOGIN_TOKEN,
    }

    session = aiohttp.ClientSession(headers=headers)
    async with session.post(LOGIN_URL, data='{}', headers={'content-type':'application/json'}) as req:
        logger.info("POST => {}".format(req.url))
        assert isinstance(req, aiohttp.ClientResponse)
        if req.status != 200:
            error = await req.json()
            session.close()
            raise RuntimeError('Failed to authenticate: %s' % error)
        else:
            result = await req.json()
            AUTH = 'Ubi_v1 t=%s' % result['ticket']
            SESSION = result['sessionId']

    session.close()

async def get_player(user_id: str, platform: str):
    platform = PLATFORM_URLS[platform]
    url = 'https://public-ubiservices.ubi.com/v1/spaces/{}/sandboxes/{}/r6playerprofile/playerprofile/progressions'.format(*platform)
    params = dict(profile_ids=user_id)
    return await get_page(url, params)

async def get_player_stats(user_id: str, platform):
    platform = PLATFORM_URLS[platform]
    spcs = [get_skill_name(n) for n in SPECIALS]
    url = 'https://public-ubiservices.ubi.com/v1/spaces/{}/sandboxes/{}/playerstats2/statistics'.format(*platform)
    params = dict(
        populations = user_id,
        statistics = 'secureareapvp_bestscore,casualpvp_matchwon,operatorpvp_timeplayed,casualpvp_matchlost,casualpvp_timeplayed,casualpvp_matchplayed,casualpvp_kills,casualpvp_death,rankedpvp_matchwon,rankedpvp_matchlost,rankedpvp_timeplayed,rankedpvp_matchplayed,rankedpvp_kills,rankedpvp_death,operatorpvp_timeplayed,{}'.format(','.join(spcs))
    )

    result = await get_page(url, params)
    if result:
        return dict((key.rsplit(':', 1)[0], value) for key, value in result['results'][user_id].items())


async def get_ranked_stats(user_id: str, platform):
    platform = PLATFORM_URLS[platform]
    url = 'https://public-ubiservices.ubi.com/v1/spaces/{}/sandboxes/{}/r6karma/players'.format(*platform)
    for region in ['emea', 'ncsa', 'apac']:
        params = dict(
            board_id = 'pvp_ranked',
            profile_ids = user_id,
            region_id = region,
            season_id = -1,
        )
        result = await get_page(url, params)
        if result and result['players'][user_id]['update_time'] != '1970-01-01T00:00:00+00:00':
            return result['players'][user_id]

SPECIALS = {
    'ASH': 'bonfirewallbreached',
    'BANDIT': 'batterykill',
    'BLACKBEARD': 'gunshieldblockdamage',
    'BLITZ': 'flashedenemy',
    'BUCK': 'kill',
    'CAPITAO': 'lethaldartkills',
    'CASTLE': 'kevlarbarricadedeployed',
    'CAVEIRA': 'interrogations',
    'DOC': 'teammaterevive',
    'ECHO': 'enemy_sonicburst_affected',
    'FROST': 'dbno',
    'FUZE': 'clusterchargekill',
    'GLAZ': 'sniperkill',
    'HIBANA': 'detonate_projectile',
    'IQ': 'gadgetspotbyef',
    'JACKAL': 'cazador_assist_kill',
    'JAGER': 'gadgetdestroybycatcher',
    'KAPKAN': 'boobytrapkill',
    'MIRA': 'black_mirror_gadget_deployed',
    'MONTAGNE': 'shieldblockdamage',
    'MUTE': 'gadgetjammed',
    'PULSE': 'heartbeatspot',
    'ROOK': 'armortakenteammate',
    'SLEDGE': 'hammerhole',
    'SMOKE': 'poisongaskill',
    'TACHANKA': 'turretkill',
    'THATCHER': 'gadgetdestroywithemp',
    'THERMITE': 'reinforcementbreached',
    'TWITCH': 'gadgetdestroybyshockdrone',
    'VALKYRIE': 'camdeployed',
}

SPECIALS_NAMES = {
    'ASH': 'Walls Breached',
    'BANDIT': 'Battery Kills',
    'BLACKBEARD': 'Damage Blocked',
    'BLITZ': 'Enemies Flahsed',
    'BUCK': 'Shotgun Kills',
    'CAPITAO': 'Lethal Dart Kills',
    'CASTLE': 'Barricades Deployed',
    'CAVEIRA': 'Interrogations',
    'DOC': 'Teammates Revived',
    'ECHO': 'Enemies Sonic Bursted',
    'FROST': 'DBNOs From Traps',
    'FUZE': 'Cluster Charge Kills',
    'GLAZ': 'Sniper Kills',
    'HIBANA': 'Projectiles Detonated',
    'IQ': 'Gadgets Spotted',
    'JACKAL': 'Footprint Scan Assists',
    'JAGER': 'Projectiles Destroyed',
    'KAPKAN': 'Boobytrap Kills',
    'MIRA': 'Black Mirrors Deployed',
    'MONTAGNE': 'Damage Blocked',
    'MUTE': 'Gadgets Jammed',
    'PULSE': 'Heartbeat Spots',
    'ROOK': 'Armor Taken',
    'SLEDGE': 'Hammer Holes',
    'SMOKE': 'Poison Gas Kills',
    'TACHANKA': 'Turret Kills',
    'THATCHER': 'Gadgets Destroyed',
    'THERMITE': 'Reinforcements Breached',
    'TWITCH': 'Gadgets Destroyed With Shock Drone',
    'VALKYRIE': 'Cameras Deployed',
}


def get_skill_name(name):
    spc = SPECIALS[name]
    if name == 'JACKEL' or name == 'MIRA':
        return 'operatorpvp_{}'.format(spc)
    else:
        return 'operatorpvp_{}_{}'.format(name.lower(), spc)