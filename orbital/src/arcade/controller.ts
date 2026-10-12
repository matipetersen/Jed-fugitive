import { type Input } from '../input/input';
import { type Audio } from '../game/audio';
import { Overlay } from '../ui/dom';
import { arcadeScreens } from '../ui/arcadeScreens';
import { type Ui } from '../ui/ui';
import { ArcadeGame } from './game';
import { type Meta, type Upgrades, buyUpgrade, loadMeta, saveMeta } from './meta';
import { RACES } from './races';
import { makeProceduralRace } from './procgen';
import { type RaceDef } from './types';
import { Mission } from './mission';
import { drawArcade, drawArcadeHud } from './render';
import { drawStars } from '../render/world';
import { type View } from '../render/view';

type Screen = 'races' | 'hub' | 'intro' | 'play' | 'cleared' | 'failed' | 'pause';

/** Menus and flow around the arcade race: hub, stage cards, results and pause. */
export class ArcadeController {
  meta: Meta = loadMeta();
  game: ArcadeGame | null = null;
  screen: Screen = 'hub';
  race: RaceDef = RACES[0];
  private width = 800;
  private height = 400;

  constructor(
    readonly overlay: Overlay,
    readonly ui: Ui,
    readonly input: Input,
    readonly audio: Audio,
    /** Leaves the arcade for the title screen. */
    readonly onExit: () => void,
  ) {}

  get mission(): Mission {
    return this.game!.mission;
  }

  resize(w: number, h: number): void {
    this.width = w;
    this.height = h;
  }

  // ----------------------------------------------------------------- flow

  /** The list of races. */
  openRaces(): void {
    this.screen = 'races';
    this.input.enabled = false;
    if (this.game) this.game.playing = false;
    saveMeta(this.meta);
    this.overlay.show(arcadeScreens.races(this));
  }

  openHub(race?: RaceDef): void {
    if (race) this.race = race;
    this.screen = 'hub';
    this.input.enabled = false;
    if (this.game) this.game.playing = false;
    saveMeta(this.meta);
    this.overlay.show(arcadeScreens.hub(this));
  }

  exit(): void {
    this.input.enabled = false;
    saveMeta(this.meta);
    this.onExit();
  }

  buy(id: keyof Upgrades): void {
    if (buyUpgrade(this.meta, id)) {
      saveMeta(this.meta);
      this.audio.chime();
      this.overlay.show(this.screen === 'cleared' ? arcadeScreens.cleared(this) : arcadeScreens.hub(this), true);
    }
  }

  openHelp(back?: () => void): void {
    this.overlay.show(arcadeScreens.help(back ?? (() => this.openHub())));
  }

  startMission(stage: number, practice: boolean): void {
    // The random race builds fresh sectors every time a real mission begins.
    if (this.race.id === 'sinfin' && !practice && stage === 0) this.race = makeProceduralRace('sinfin', Math.floor(Math.random() * 1e9));
    const m = new Mission(this.meta, { stage, practice, race: this.race });
    if (this.game) this.game.setMission(m);
    else this.game = new ArcadeGame(this.meta, this.input, this.ui, this.audio, m);
    this.game.playing = false;
    this.game.autoAim = false;
    this.input.reset();
    this.input.zoom = 0.8;
    this.input.zoomManual = false;
    this.openIntro();
  }

  openIntro(): void {
    this.screen = 'intro';
    this.input.enabled = false;
    if (this.game) this.game.playing = false;
    this.overlay.show(arcadeScreens.intro(this));
  }

  openPauseExit(): void {
    this.overlay.show(arcadeScreens.confirmExit(this));
  }

  begin(): void {
    this.overlay.hide();
    this.screen = 'play';
    this.input.enabled = true;
    this.input.reset();
    this.game!.playing = true;
  }

  resume(): void {
    this.begin();
  }

  openPause(): void {
    this.screen = 'pause';
    this.input.enabled = false;
    this.game!.playing = false;
    this.overlay.show(arcadeScreens.pause(this));
  }

  retry(): void {
    this.mission.retry();
    this.game!.setMission(this.mission);
    this.openIntro();
  }

  nextStage(): void {
    if (this.mission.nextStage()) {
      this.game!.setMission(this.mission);
      this.input.reset();
      saveMeta(this.meta);
      this.openIntro();
    }
  }

  abandon(): void {
    const m = this.mission;
    m.abandon();
    this.openHub();
  }

  // ---------------------------------------------------------------- frame

  /** Per-frame update and draw. */
  frame(ctx: CanvasRenderingContext2D, now: number, dt: number, dpr: number): void {
    const g = this.game;
    ctx.globalCompositeOperation = 'source-over';
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.fillStyle = '#02020a';
    ctx.fillRect(0, 0, this.width, this.height);
    ctx.globalCompositeOperation = 'lighter';
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    if (!g) {
      const v: View = { cx: now * 8, cy: 0, zoom: 1, up: Math.PI / 2, w: this.width, h: this.height };
      drawStars(ctx, v);
      return;
    }
    g.update(dt, now / 1000);
    if (g.pauseRequested) {
      g.pauseRequested = false;
      if (this.screen === 'play') this.openPause();
    }
    this.detectEnd();
    drawArcade(ctx, g, this.width, this.height);
    if (this.screen === 'play') drawArcadeHud(ctx, g, this.width, this.height);
    g.ui.commit();
  }

  private detectEnd(): void {
    const m = this.mission;
    if (this.screen !== 'play') return;
    if (m.phase === 'cleared' && m.result) {
      this.screen = 'cleared';
      this.input.enabled = false;
      this.game!.playing = false;
      saveMeta(this.meta);
      this.audio.chime();
      this.overlay.show(arcadeScreens.cleared(this));
    } else if (m.phase === 'failed') {
      this.screen = 'failed';
      this.input.enabled = false;
      this.game!.playing = false;
      saveMeta(this.meta);
      this.audio.alarm();
      this.overlay.show(arcadeScreens.failed(this));
    }
  }
}
