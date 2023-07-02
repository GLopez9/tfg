import 'chessground/assets/chessground.base.css';
import 'chessground/assets/chessground.brown.css';
import { Field } from '@mliebelt/pgn-reader';
import { PgnViewerConfiguration } from "./types";
/**
 * This implements the base function that is used to display a board, a whole game
 * or even allow to play it.
 * See the other functions and their implementation how to use the building blocks
 * of pgnBase to build new functionality. The configuration here is the super-set
 * of all the configurations of the other functions.
 */
declare let pgnBase: (boardId: string, configuration: PgnViewerConfiguration) => {
    chess: any;
    board: import("chessground/api").Api;
    getPgn: () => import("../pgn-reader/lib").PgnReader;
    generateHTML: () => void;
    generateBoard: () => import("chessground/api").Api;
    generateMoves: () => void;
    manualMove: (san: string) => void;
    onSnapEnd: (from: Field, to: Field, meta: any) => void;
    resizeLayout: () => void;
    t: (term: string) => string;
};
export { pgnBase };
//# sourceMappingURL=pgnv.d.ts.map