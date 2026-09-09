"""
Phase 4.5 P0 Hardening — Deterministic 2D Spatial Layout & Line Clustering Engine
================================================================================
Converts raw OCR tokens with bounding boxes into structured 2D lines and blocks.
Enables spatial label -> value association across horizontal baselines and
vertically stacked multiline packaging layouts.

Architectural Principles:
1. Deterministic Geometry: Clusters tokens strictly using coordinates, heights,
   and baseline alignment without probabilistic inference.
2. Provenance Preservation: Retains original bounding boxes, token confidences,
   and character offsets for every clustered line and block.
3. Non-Adjudicative: Provides structured spatial layout evidence; does not make
   statutory compliance decisions.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class SpatialToken:
    text: str
    conf: Optional[float]
    bbox: Tuple[int, int, int, int]  # (left, top, width, height)
    line_num: int = 0
    block_num: int = 0

    @property
    def left(self) -> int:
        return self.bbox[0]

    @property
    def top(self) -> int:
        return self.bbox[1]

    @property
    def width(self) -> int:
        return self.bbox[2]

    @property
    def height(self) -> int:
        return self.bbox[3]

    @property
    def right(self) -> int:
        return self.bbox[0] + self.bbox[2]

    @property
    def bottom(self) -> int:
        return self.bbox[1] + self.bbox[3]

    @property
    def center_x(self) -> float:
        return self.bbox[0] + (self.bbox[2] / 2.0)

    @property
    def center_y(self) -> float:
        return self.bbox[1] + (self.bbox[3] / 2.0)


@dataclass
class SpatialLine:
    line_id: int
    tokens: List[SpatialToken]
    text: str
    bbox: Tuple[int, int, int, int]  # (left, top, width, height)
    block_num: int = 0

    @property
    def left(self) -> int:
        return self.bbox[0]

    @property
    def top(self) -> int:
        return self.bbox[1]

    @property
    def width(self) -> int:
        return self.bbox[2]

    @property
    def height(self) -> int:
        return self.bbox[3]

    @property
    def right(self) -> int:
        return self.bbox[0] + self.bbox[2]

    @property
    def bottom(self) -> int:
        return self.bbox[1] + self.bbox[3]

    @property
    def avg_token_height(self) -> float:
        if not self.tokens:
            return float(self.height)
        return sum(t.height for t in self.tokens) / len(self.tokens)


@dataclass
class SpatialBlock:
    block_id: int
    lines: List[SpatialLine]
    text: str
    bbox: Tuple[int, int, int, int]

    @property
    def left(self) -> int:
        return self.bbox[0]

    @property
    def top(self) -> int:
        return self.bbox[1]

    @property
    def width(self) -> int:
        return self.bbox[2]

    @property
    def height(self) -> int:
        return self.bbox[3]

    @property
    def right(self) -> int:
        return self.bbox[0] + self.bbox[2]

    @property
    def bottom(self) -> int:
        return self.bbox[1] + self.bbox[3]


@dataclass
class SpatialLayoutResult:
    lines: List[SpatialLine] = field(default_factory=list)
    blocks: List[SpatialBlock] = field(default_factory=list)
    full_text: str = ""

    def get_lines_text(self) -> List[str]:
        return [l.text for l in self.lines]

    def get_blocks_text(self) -> List[str]:
        return [b.text for b in self.blocks]


def build_spatial_layout(tokens_data: Optional[List[Dict[str, Any]]]) -> SpatialLayoutResult:
    """
    Constructs a deterministic 2D spatial layout from OCR tokens_data.
    Groups tokens into lines and lines into blocks, preserving exact geometry.
    """
    if not tokens_data:
        return SpatialLayoutResult()

    # 1. Parse raw token dictionaries into SpatialToken instances
    parsed_tokens: List[SpatialToken] = []
    for item in tokens_data:
        raw_text = str(item.get("text", "")).strip()
        if not raw_text:
            continue
        bbox_list = item.get("bbox", [0, 0, 0, 0])
        if len(bbox_list) == 4:
            bbox = (int(bbox_list[0]), int(bbox_list[1]), int(bbox_list[2]), int(bbox_list[3]))
        else:
            bbox = (0, 0, 0, 0)

        conf = item.get("conf")
        if conf is not None:
            try:
                conf = float(conf)
            except (ValueError, TypeError):
                conf = None

        parsed_tokens.append(
            SpatialToken(
                text=raw_text,
                conf=conf,
                bbox=bbox,
                line_num=int(item.get("line_num", 0)),
                block_num=int(item.get("block_num", 0)),
            )
        )

    if not parsed_tokens:
        return SpatialLayoutResult()

    # 2. Group tokens into lines
    # If line_num is provided and discriminative, group by (block_num, line_num)
    # Otherwise fallback to baseline clustering.
    line_groups: Dict[Tuple[int, int], List[SpatialToken]] = {}
    has_valid_line_nums = any(t.line_num > 0 for t in parsed_tokens)

    if has_valid_line_nums:
        for t in parsed_tokens:
            key = (t.block_num, t.line_num)
            line_groups.setdefault(key, []).append(t)
    else:
        # Baseline clustering: sort by top coordinate, group if vertical distance < 0.5 * height
        sorted_by_y = sorted(parsed_tokens, key=lambda t: (t.top, t.left))
        current_group: List[SpatialToken] = []
        group_idx = 1
        for t in sorted_by_y:
            if not current_group:
                current_group.append(t)
            else:
                last_t = current_group[-1]
                v_diff = abs(t.center_y - last_t.center_y)
                avg_h = (t.height + last_t.height) / 2.0
                if v_diff <= max(8.0, avg_h * 0.5):
                    current_group.append(t)
                else:
                    line_groups[(0, group_idx)] = current_group
                    group_idx += 1
                    current_group = [t]
        if current_group:
            line_groups[(0, group_idx)] = current_group

    spatial_lines: List[SpatialLine] = []
    line_id = 1
    # Sort groups by minimum top coordinate
    sorted_group_keys = sorted(
        line_groups.keys(),
        key=lambda k: min(t.top for t in line_groups[k]),
    )

    for k in sorted_group_keys:
        tokens_in_line = sorted(line_groups[k], key=lambda t: t.left)
        min_left = min(t.left for t in tokens_in_line)
        min_top = min(t.top for t in tokens_in_line)
        max_right = max(t.right for t in tokens_in_line)
        max_bottom = max(t.bottom for t in tokens_in_line)
        w = max_right - min_left
        h = max_bottom - min_top
        line_text = " ".join(t.text for t in tokens_in_line)
        spatial_lines.append(
            SpatialLine(
                line_id=line_id,
                tokens=tokens_in_line,
                text=line_text,
                bbox=(min_left, min_top, w, h),
                block_num=k[0],
            )
        )
        line_id += 1

    # 3. Group lines into blocks
    # Lines with small vertical gap and overlapping horizontal extent belong to same block
    spatial_blocks: List[SpatialBlock] = []
    if spatial_lines:
        curr_block_lines: List[SpatialLine] = [spatial_lines[0]]
        block_id = 1

        for line in spatial_lines[1:]:
            prev_line = curr_block_lines[-1]
            vertical_gap = line.top - prev_line.bottom
            max_allowed_gap = max(prev_line.avg_token_height * 2.0, 30.0)

            # Check horizontal overlap
            h_overlap = not (line.right < prev_line.left - 50 or line.left > prev_line.right + 50)

            # Same block_num from OCR or spatially proximate
            same_block = (line.block_num > 0 and line.block_num == prev_line.block_num) or (
                vertical_gap >= -10 and vertical_gap <= max_allowed_gap and h_overlap
            )

            if same_block:
                curr_block_lines.append(line)
            else:
                b_min_l = min(l.left for l in curr_block_lines)
                b_min_t = min(l.top for l in curr_block_lines)
                b_max_r = max(l.right for l in curr_block_lines)
                b_max_b = max(l.bottom for l in curr_block_lines)
                b_text = "\n".join(l.text for l in curr_block_lines)
                spatial_blocks.append(
                    SpatialBlock(
                        block_id=block_id,
                        lines=curr_block_lines,
                        text=b_text,
                        bbox=(b_min_l, b_min_t, b_max_r - b_min_l, b_max_b - b_min_t),
                    )
                )
                block_id += 1
                curr_block_lines = [line]

        if curr_block_lines:
            b_min_l = min(l.left for l in curr_block_lines)
            b_min_t = min(l.top for l in curr_block_lines)
            b_max_r = max(l.right for l in curr_block_lines)
            b_max_b = max(l.bottom for l in curr_block_lines)
            b_text = "\n".join(l.text for l in curr_block_lines)
            spatial_blocks.append(
                SpatialBlock(
                    block_id=block_id,
                    lines=curr_block_lines,
                    text=b_text,
                    bbox=(b_min_l, b_min_t, b_max_r - b_min_l, b_max_b - b_min_t),
                )
            )

    full_text = "\n".join(b.text for b in spatial_blocks) if spatial_blocks else "\n".join(l.text for l in spatial_lines)

    return SpatialLayoutResult(
        lines=spatial_lines,
        blocks=spatial_blocks,
        full_text=full_text,
    )

