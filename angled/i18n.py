"""English / Japanese strings.  Use T("key", **fmt)."""

STRINGS = {
    # ---------------------------------------------------------------- title
    "title_sub": ("Pop it at the right angle!", "かくどを あわせて ポン！"),
    "menu_start": ("Start Game", "ゲームスタート"),
    "menu_continue": ("Continue  (Level {n})", "つづきから （レベル {n}）"),
    "menu_battle": ("VS CPU Battle", "CPUと たいせん"),
    "menu_difficulty": ("Difficulty", "むずかしさ"),
    "menu_name": ("Name", "なまえ"),
    "menu_lang": ("Language", "ことば"),
    "menu_bgm": ("BGM", "BGM"),
    "menu_parents": ("For Parents", "保護者の方へ"),
    "menu_credits": ("Credits", "クレジット"),
    "menu_quit": ("Quit", "おわる"),
    "lang_name": ("English", "日本語"),
    "on": ("ON", "オン"),
    "off": ("OFF", "オフ"),
    "easy": ("Easy", "かんたん"),
    "normal": ("Normal", "ふつう"),
    "hard": ("Hard", "むずかしい"),
    "top10": ("TOP 10", "ランキング TOP10"),
    "no_scores": ("No scores yet - be the first!", "まだ きろくが ないよ！"),
    "name_edit_hint": ("Type your name, then press ENTER", "なまえを いれて ENTER"),
    "title_hint": ("↑↓ choose   ←→ change   ENTER select", "↑↓ えらぶ   ←→ かえる   ENTER けってい"),
    "player": ("Player", "プレイヤー"),
    "lv": ("Lv", "Lv"),

    # ---------------------------------------------------------------- HUD
    "level": ("LEVEL", "レベル"),
    "score": ("SCORE", "スコア"),
    "hiscore": ("HI-SCORE", "ハイスコア"),
    "time": ("TIME", "タイム"),
    "combo": ("COMBO", "コンボ"),
    "angle": ("ANGLE", "かくど"),
    "difficulty": ("DIFFICULTY", "むずかしさ"),
    "guide_on": ("Guide line ON (Levels 1-10)", "ガイドせん オン（レベル1〜10）"),
    "guide_off": ("No guide line - trust your angles!", "ガイドなし！ かくどを よもう！"),
    "ctl_title": ("CONTROLS", "そうさ"),
    "ctl_1": ("← → / A D : turn the arrow", "← → / A D ： やじるしを まわす"),
    "ctl_2": ("SPACE / ↑ / click : shoot", "スペース / ↑ / クリック ： うつ"),
    "ctl_3": ("SHIFT + ← → : 5° steps", "SHIFT + ← → ： 5°ずつ"),
    "ctl_4": ("Hold ← → to turn faster", "← → ながおしで はやく まわる"),
    "ctl_5": ("Mouse aims, wheel = 1°", "マウスで ねらう・ホイールで 1°"),
    "ctl_6": ("ESC / P : pause", "ESC / P ： ポーズ"),
    "rule_1": ("Strike each bubble at the", "バブルの ふちの"),
    "rule_2": ("spot written inside it!", "かいてある かくどに あてよう！"),
    "rule_3": ("Read the spot around the bubble:", "バブルの まわりで よもう："),
    "rule_4": ("right 0°  bottom 90°  left 180°", "みぎ0°  した90°  ひだり180°"),
    "ready": ("LEVEL {n}", "レベル {n}"),
    "ready2": ("READY?", "よーい…"),
    "go": ("GO!", "スタート！"),
    "clear": ("LEVEL CLEAR!", "レベル クリア！"),
    "time_bonus": ("Time bonus  {n}", "タイムボーナス  {n}"),
    "level_bonus": ("Level bonus  {n}", "レベルボーナス  {n}"),
    "time_up": ("TIME UP!", "タイムアップ！"),
    "floor_hit": ("THE BUBBLES REACHED THE FLOOR!", "バブルが ゆかに ついた！"),
    "game_over": ("GAME OVER", "ゲームオーバー"),
    "wrong": ("WRONG ANGLE!", "かくどが ちがうよ！"),
    "wrong_detail": ("needs {a}°  -  you struck {b}°", "{a}° が ひつよう ・ いまは {b}°"),
    "bank": ("BANK SHOT x{n}!", "バンクショット x{n}！"),
    "nice": ("NICE!", "ナイス！"),
    "great": ("GREAT!", "すごい！"),
    "drop": ("DROP! +{n}", "おとした！ +{n}"),
    "miss": ("MISS", "ミス"),
    "paused": ("PAUSED", "ポーズちゅう"),
    "resume": ("Resume", "つづける"),
    "to_title": ("Quit to Title", "タイトルへ もどる"),
    "press_key": ("Press ENTER", "ENTERを おしてね"),
    "final_level": ("FINAL LEVEL 100!", "さいごの レベル100！"),

    # ---------------------------------------------------------------- celebration
    "congrats": ("CONGRATULATIONS!", "おめでとう！"),
    "congrats_99": ("You cleared 99 levels!", "99レベル クリア！"),
    "congrats_more": ("One last challenge awaits: Level 100!", "さいごの ちょうせん レベル100が まってるよ！"),
    "all_clear": ("ALL 100 LEVELS CLEAR!", "ぜんぶ クリア！ 100レベル せいは！"),
    "all_clear2": ("You are an Angle Master!", "きみは かくどマスター！"),

    # ---------------------------------------------------------------- name entry
    "new_record": ("NEW HIGH SCORE!", "ハイスコア！"),
    "rank_n": ("Rank #{n}", "{n} い"),
    "enter_name": ("Enter your name and press ENTER", "なまえを いれて ENTERを おしてね"),
    "final_score": ("Score {s}   Level {l}", "スコア {s}   レベル {l}"),

    # ---------------------------------------------------------------- battle
    "you": ("YOU", "あなた"),
    "cpu": ("CPU", "CPU"),
    "you_win": ("YOU WIN!", "あなたの かち！"),
    "cpu_wins": ("CPU WINS...", "CPUの かち…"),
    "draw": ("DRAW", "ひきわけ"),
    "battle_rule": ("Popped bubbles fly to your opponent!", "わったバブルは あいてに とんでいく！"),
    "battle_end": ("ENTER rematch    ESC title", "ENTER もういちど    ESC タイトル"),
    "bubbles_left": ("Bubbles: {n}", "のこり: {n}"),
    "wins": ("Wins {a} - {b}", "{a} しょう - {b} しょう"),

    # ---------------------------------------------------------------- credits
    "credits": ("CREDITS", "クレジット"),
    "created_by": ("Created by", "せいさく"),
    "studio": ("A game by", "はっこう"),
    "version": ("Version", "バージョン"),
    "build": ("Build", "ビルド"),
    "build_date": ("Date", "日付"),
    "third_party": ("Third-party assets", "使用素材"),
    "tp_pop": ("Pop sounds: BigSoundBank (Joseph Sardin), CC0", "ポップ音：BigSoundBank（Joseph Sardin） CC0"),
    "tp_font": ("Fonts: DejaVu Sans, Droid Sans Fallback (Apache 2.0)", "フォント：DejaVu Sans / Droid Sans Fallback（Apache 2.0）"),
    "tp_pygame": ("Engine: pygame (LGPL)", "エンジン：pygame（LGPL）"),
    "back": ("ESC  back", "ESC  もどる"),

    # ---------------------------------------------------------------- parents
    "parents": ("FOR PARENTS", "保護者の方へ"),
    "gate_q": ("Parents only: please answer to continue", "保護者の方：答えを入力して続けてください"),
    "gate_wrong": ("Not quite - try again.", "ちがいます。もう一度どうぞ。"),
    "all_players": ("All players", "全員"),
    "total_time": ("Total play time", "合計プレイ時間"),
    "today": ("Today", "今日"),
    "week": ("Last 7 days", "過去7日間"),
    "games": ("Games played", "プレイ回数"),
    "best_score": ("Best score", "最高スコア"),
    "best_level": ("Highest level", "最高到達レベル"),
    "accuracy": ("Accuracy", "命中率"),
    "recent": ("Recent games", "最近のプレイ"),
    "failed_levels": ("Most-failed levels", "よく失敗するレベル"),
    "chart_title": ("Level reached in each game (last 30)", "プレイごとの到達レベル（直近30回）"),
    "h_date": ("Date", "日時"),
    "h_mode": ("Mode", "モード"),
    "h_diff": ("Diff.", "難易度"),
    "h_result": ("Result", "結果"),
    "h_score": ("Score", "スコア"),
    "h_time": ("Time", "時間"),
    "mode_single": ("Solo", "ひとり"),
    "mode_battle": ("VS CPU", "対CPU"),
    "res_time": ("Failed Lv {n} (time up)", "Lv{n}で失敗（時間切れ）"),
    "res_floor": ("Failed Lv {n} (bubbles hit floor)", "Lv{n}で失敗（床に到達）"),
    "res_quit": ("Quit at Lv {n}", "Lv{n}で中断"),
    "res_allclear": ("ALL CLEAR (Lv 100)", "全クリア（Lv100）"),
    "res_win": ("Battle: won", "対戦：勝ち"),
    "res_lose": ("Battle: lost", "対戦：負け"),
    "res_draw": ("Battle: draw", "対戦：引き分け"),
    "res_bquit": ("Battle: quit", "対戦：中断"),
    "leg_time": ("Time up", "時間切れ"),
    "leg_floor": ("Reached floor", "床に到達"),
    "leg_quit": ("Quit", "中断"),
    "leg_clear": ("All clear", "全クリア"),
    "none_yet": ("No games recorded yet.", "まだ記録がありません。"),
    "parents_hint": ("←→ player   ↑↓ scroll   DEL reset data   ESC back",
                     "←→ プレイヤー   ↑↓ スクロール   DEL データ削除   ESC 戻る"),
    "reset_confirm": ("Press DEL again to erase ALL play data", "もう一度DELで全データを削除します"),
    "reset_done": ("All play data erased.", "データを削除しました。"),
    "hm": ("{h}h {m}m", "{h}時間{m}分"),
    "ms": ("{m}m {s}s", "{m}分{s}秒"),
}

_lang = "en"


def set_lang(lang):
    global _lang
    _lang = "ja" if lang == "ja" else "en"


def get_lang():
    return _lang


def T(key, **fmt):
    pair = STRINGS.get(key)
    if pair is None:
        return key
    s = pair[1] if _lang == "ja" else pair[0]
    if fmt:
        try:
            s = s.format(**fmt)
        except Exception:
            pass
    return s
