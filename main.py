import itertools, copy
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np

class Table:
    def __init__(self, init):
        if isinstance(init, int):
            self.n = init
            self.internal = [[0 for _ in range(init)] for _ in range(init)]
        elif isinstance(init, list):
            self.n = len(init)
            self.internal = copy.deepcopy(init)
        else:
            raise NotImplemented

    def show(self):
        for line in self.internal:
            print(line)

    def count(self):
        count = 0
        for line in self.internal:
            count += sum([1 if masu > 0 else 0 for masu in line])
        return count

    def set(self, x, y, val):
        if not 0 <= x < self.n:
            raise IndexError()
        if not 0 <= y < self.n:
            raise IndexError()
        self.internal[self.n - y - 1][x] = val

    def get(self, x, y):
        if not 0 <= x < self.n:
            raise IndexError()
        if not 0 <= y < self.n:
            raise IndexError()
        return self.internal[self.n - y - 1][x]

    # --- matplotlibによる可視化メソッド ---
    def visualize(self, xans=None, yans=None, show=True):
        n = self.n
        # (0,0)を左下にするため、internal(上から下)を逆順にしてnumpy配列化
        data = np.array(self.internal)[::-1]

        fig, ax = plt.subplots(figsize=(8, 8))

        # カラーマップの準備 (ピース用)
        cmap_base = plt.get_cmap('tab20')

        # セルごとに描画
        for y in range(n):
            for x in range(n):
                val = data[y, x]
                color = 'white'
                label = str(val)
                text_color = 'black'

                if val == 0:
                    color = 'white'
                    label = ''
                elif val == 1:
                    color = '#333333' # Dark Gray/Black
                    label = '1'
                    text_color = 'white'
                elif val == -1:
                    color = '#D3D3D3' # Light Gray
                    label = '-1'
                else:
                    # マテリアルID (2~) はカラーマップから色を取得
                    # 色が被らないようにインデックスを調整
                    color = cmap_base((val - 2) % 20)

                # 四角形を描画
                rect = plt.Rectangle((x, y), 1, 1, facecolor=color, edgecolor='black', linewidth=1.5)
                ax.add_patch(rect)

                # 数字を描画
                ax.text(x + 0.5, y + 0.5, label, ha='center', va='center',
                        color=text_color, fontsize=14, fontweight='bold')

        # 軸の設定 (0.5刻みにしてグリッドの中心に数字が来るように調整)
        ax.set_xlim(0, n)
        ax.set_ylim(0, n)
        ax.set_xticks(np.arange(n) + 0.5)
        ax.set_yticks(np.arange(n) + 0.5)
        ax.set_xticklabels(range(n)) # X座標 (0, 1, 2...)
        ax.set_yticklabels(range(n)) # Y座標 (0, 1, 2...)

        ax.set_xlabel("X Axis")
        ax.set_ylabel("Y Axis")
        ax.set_aspect('equal')

        # --- 正解データ(ターゲット合計値)の表示 ---
        if xans:
            # 上側のX軸に合計値を表示
            sec_ax_x = ax.secondary_xaxis('top')
            sec_ax_x.set_xticks(np.arange(n) + 0.5)
            sec_ax_x.set_xticklabels(xans, color='blue', fontweight='bold')
            sec_ax_x.set_xlabel("Target X Sums", color='blue')

        if yans:
            # 右側のY軸に合計値を表示
            # yans配列は[TopRow, ..., BottomRow]の順なので、表示用に逆順にする
            sec_ax_y = ax.secondary_yaxis('right')
            sec_ax_y.set_yticks(np.arange(n) + 0.5)
            sec_ax_y.set_yticklabels(yans[::-1], color='blue', fontweight='bold')
            sec_ax_y.set_ylabel("Target Y Sums", color='blue')

        plt.title("Puzzle Result", fontsize=16, pad=20)
        
        if show:
            plt.show()
        else:
            return fig

    def eval(self, xans: list, yans: list, mats: list):
        if len(xans) != self.n or len(yans) != self.n:
            raise ValueError()

        # count()は正の値のみ数える仕様
        if sum(xans) != sum(yans) or sum(xans) != sum(mats) + self.count():
            raise ValueError(f"Sum Mismatch. X:{sum(xans)} Y:{sum(yans)} Blocks:{sum(mats) + self.count()}")

        print("OK: Starting Optimized Solver...")

        # --- Solver Setup ---
        n = self.n

        # 盤面の初期状態スキャン
        obstacle_mask = 0
        current_x_counts = [0] * n
        current_y_counts = [0] * n # index 0 is top row (y=n-1)

        for r in range(n):
            for c in range(n):
                val = self.internal[r][c]
                if val != 0:
                    # 1 も -1 も配置不可場所としてマスク
                    obstacle_mask |= (1 << (r * n + c))
                    if val > 0: # 1だけカウント
                        current_x_counts[c] += 1
                        current_y_counts[r] += 1

        # 初期チェック
        for i in range(n):
            if current_x_counts[i] > xans[i] or current_y_counts[i] > yans[i]:
                print("Impossible: Initial board exceeds constraints.")
                return

        # ピース配置の事前計算
        print(f"[Progress] Calculating piece placement options... (Pieces: {len(mats)})")
        placement_options = []
        for mat_idx, mat in enumerate(mats):
            options = []
            for rot_idx in range(4):
                rotated_mat = mat.rotate(rot_idx)
                for dy in range(n):
                    for dx in range(n):
                        mask = 0
                        possible = True
                        x_adds = [0] * n
                        y_adds = [0] * n

                        for px, py in rotated_mat.positions:
                            tx, ty = px + dx, py + dy
                            if not (0 <= tx < n and 0 <= ty < n):
                                possible = False
                                break
                            r = n - ty - 1 # y to row index
                            c = tx
                            mask |= (1 << (r * n + c))
                            x_adds[c] += 1
                            y_adds[r] += 1

                        if possible:
                            if (mask & obstacle_mask) == 0:
                                options.append({
                                    'mask': mask,
                                    'x_adds': x_adds,
                                    'y_adds': y_adds,
                                    'rot': rot_idx,
                                    'dx': dx,
                                    'dy': dy
                                })
            if not options:
                print(f"Material {mat_idx} cannot be placed.")
                return
            placement_options.append(options)
            print(f"[Progress] Piece {mat_idx + 1}/{len(mats)}: Generated {len(options)} placement options")

        print(f"[Progress] Placement options calculation complete. Starting DFS search...")

        # DFS
        solution_history = [None] * len(mats)
        found = False
        iteration_count = [0]  # リストで包んでnonlocalとして使用
        log_interval = 20000  # 2万イテレーションごとにログ出力

        def solve(idx, current_mask, cur_x, cur_y):
            nonlocal found
            if found: return
            
            # イテレーションカウント
            iteration_count[0] += 1
            if iteration_count[0] % log_interval == 0:
                print(f"[Progress] DFS search: {iteration_count[0]:,} iterations (Current depth: {idx}/{len(mats)})")
            
            if idx == len(mats):
                found = True
                return

            for opt in placement_options[idx]:
                if found: return
                if (current_mask & opt['mask']) != 0:
                    continue

                # 枝刈り: X合計チェック
                next_x = cur_x[:]
                valid_x = True
                for i in range(n):
                    next_x[i] += opt['x_adds'][i]
                    if next_x[i] > xans[i]:
                        valid_x = False; break
                if not valid_x: continue

                # 枝刈り: Y合計チェック
                next_y = cur_y[:]
                valid_y = True
                for i in range(n):
                    next_y[i] += opt['y_adds'][i]
                    if next_y[i] > yans[i]:
                        valid_y = False; break
                if not valid_y: continue

                solution_history[idx] = opt
                solve(idx + 1, current_mask | opt['mask'], next_x, next_y)

        solve(0, obstacle_mask, current_x_counts, current_y_counts)
        
        print(f"[Progress] DFS search complete. Total iterations: {iteration_count[0]:,}")

        if found:
            print("Placed! Visualizing...")
            for i, opt in enumerate(solution_history):
                rotated_mat = mats[i].rotate(opt['rot'])
                val = i + 2
                for px, py in rotated_mat.positions:
                    self.set(px + opt['dx'], py + opt['dy'], val)

            # --- ここで可視化を呼び出し ---
            # self.visualize(xans, yans)
            return self
        else:
            print("No solution found.")
            return None



class Material:
    def __init__(self, positions: list):
        self.positions = positions
        self.n = len(positions)
    def show(self):
        # 簡易表示用（ロジックには影響なし）
        pass
    def __add__(self, other):
        if isinstance(other, Material): return self.n + other.n
        if isinstance(other, int): return self.n + other
        return NotImplemented
    def __radd__(self, other):
        return self.__add__(other)
    def rotate(self, count):
        positions = self.positions[:]
        for _ in range(count):
            positions = [(y, -x) for x, y in positions]
        return Material(positions)

if __name__ == "__main__":
    t = Table(5)
    mats = [
        Material([(0, 0), (0, 1), (1, 1)]),
        Material([(0, 0), (1, 0), (1, 1), (2, 0)]),
        Material([(0, 0), (1, 0), (2, 0), (2, -1)]),
        Material([(0, 0), (1, 0), (1, 1), (2, 1)])
    ]

    t.eval(
        [5, 4, 3, 2, 1],
        [5, 4, 3, 2, 1],
        mats
    )

"""
if __name__ == "__main__":
    t = Table(6)
    # 初期配置
    t.set(0, 0, 1)
    t.set(1, 0, 1)
    t.set(2, 1, 1)
    t.set(4, 2, 1)
    t.set(2, 4, 1)
    t.set(0, 5, -1)
    t.set(5, 0, -1)

    # マテリアル定義
    mats = [
        Material([(0, 0), (0, 1), (1, 0), (2, 0), (2, 1), (2, 2)]),
        Material([(0, 0), (0, 1), (1, 1), (1, 2), (2, 2)]),
        Material([(0, 0), (1, 0), (-1, 1), (0, 1), (1, 1), (-1, 2), (0, 2)]),
        Material([(0, 0), (1, 0), (2, 0), (2, 1), (2, 2)]),
    ]

    # 実行
    t.eval(
        [2, 6, 5, 5, 5, 5], # xans
        [5, 5, 5, 5, 6, 2], # yans
        mats
    )
    """

if 1 == 1: pass