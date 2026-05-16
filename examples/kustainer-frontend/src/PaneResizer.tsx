import { useCallback, useEffect, useRef } from "react";

interface Props {
  onDrag: (deltaY: number) => void;
}

export function PaneResizer({ onDrag }: Props) {
  const draggingRef = useRef(false);
  const lastYRef = useRef(0);
  const onDragRef = useRef(onDrag);
  onDragRef.current = onDrag;

  const handlePointerDown = useCallback((e: React.PointerEvent<HTMLDivElement>) => {
    e.preventDefault();
    draggingRef.current = true;
    lastYRef.current = e.clientY;
    document.body.style.cursor = "row-resize";
    document.body.style.userSelect = "none";
    (e.target as HTMLElement).setPointerCapture(e.pointerId);
  }, []);

  const handlePointerMove = useCallback((e: React.PointerEvent<HTMLDivElement>) => {
    if (!draggingRef.current) return;
    const delta = e.clientY - lastYRef.current;
    lastYRef.current = e.clientY;
    if (delta !== 0) onDragRef.current(delta);
  }, []);

  const endDrag = useCallback((e: React.PointerEvent<HTMLDivElement>) => {
    if (!draggingRef.current) return;
    draggingRef.current = false;
    document.body.style.cursor = "";
    document.body.style.userSelect = "";
    (e.target as HTMLElement).releasePointerCapture?.(e.pointerId);
  }, []);

  // Safety: drop cursor overrides if the component unmounts mid-drag.
  useEffect(() => {
    return () => {
      document.body.style.cursor = "";
      document.body.style.userSelect = "";
    };
  }, []);

  return (
    <div
      className="pane-resizer"
      role="separator"
      aria-orientation="horizontal"
      onPointerDown={handlePointerDown}
      onPointerMove={handlePointerMove}
      onPointerUp={endDrag}
      onPointerCancel={endDrag}
    />
  );
}
