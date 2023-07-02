declare class Timer {
    private _notifications;
    private _resolution;
    private _running;
    private _ticks;
    private _timer;
    private _drift;
    constructor(resolution: number);
    start(): Timer;
    stop(): this;
    reset(): this;
    clear(): this;
    ticks(): number;
    resolution(): number;
    running(): boolean;
    bind(when: number, callback: any): this;
    unbind(callback: any): this;
    drift(timeDrift: number): this;
}
export default Timer;
//# sourceMappingURL=timer.d.ts.map