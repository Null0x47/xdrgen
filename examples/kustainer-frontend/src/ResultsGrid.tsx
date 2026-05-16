import { useMemo } from "react";
import { AgGridReact } from "ag-grid-react";
import { type ColDef } from "ag-grid-community";

import "ag-grid-community/styles/ag-grid.css";
import "ag-grid-community/styles/ag-theme-quartz.css";

import type { QueryResult } from "./kustainer";

interface Props {
  result: QueryResult | null;
  theme: "light" | "dark";
  onRowClick: (row: Record<string, unknown>) => void;
}

export function ResultsGrid({ result, theme, onRowClick }: Props) {
  const columnDefs = useMemo<ColDef[]>(() => {
    if (!result) return [];
    return result.columns.map((c) => ({
      field: c.name,
      headerName: c.name,
      headerTooltip: `${c.name} (${c.type})`,
      sortable: true,
      filter: false,
      resizable: true,
    }));
  }, [result]);

  const rowData = useMemo(() => {
    if (!result) return [];
    return result.rows.map((row) => {
      const obj: Record<string, unknown> = {};
      result.columns.forEach((c, i) => {
        const v = row[i];
        obj[c.name] = v && typeof v === "object" ? JSON.stringify(v) : v;
      });
      return obj;
    });
  }, [result]);

  if (!result) {
    return <div className="grid-empty">Run a query to see results.</div>;
  }

  const themeClass = theme === "dark" ? "ag-theme-quartz-dark" : "ag-theme-quartz";

  return (
    <div className={themeClass} style={{ height: "100%", width: "100%" }}>
      <AgGridReact
        columnDefs={columnDefs}
        rowData={rowData}
        defaultColDef={{ flex: 1, minWidth: 120 }}
        animateRows={false}
        pagination={true}
        paginationPageSize={100}
        paginationPageSizeSelector={false}
        onRowClicked={(e) =>
          e.data && onRowClick(e.data as Record<string, unknown>)
        }
      />
    </div>
  );
}
