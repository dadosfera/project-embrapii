import { useState } from "react";

import {
  type ColumnDef,
  flexRender,
  getCoreRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  type SortingState,
  useReactTable,
} from "@tanstack/react-table";

import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { EmptyState } from "@/ui/EmptyState";

type DataTableProps<TData> = {
  data: TData[];
  columns: ColumnDef<TData, unknown>[];
  emptyMessage?: string;
  pageSize?: number;
};

function alinhamento(meta?: { align?: string; priority?: string }) {
  return [
    meta?.align === "right" ? "text-right tabular-nums" : "text-left",
    meta?.priority === "low" ? "hidden lg:table-cell" : "",
  ].join(" ");
}

export function DataTable<TData>({
  data,
  columns,
  emptyMessage = "Nenhum registro encontrado.",
  pageSize = 10,
}: DataTableProps<TData>) {
  const [sorting, setSorting] = useState<SortingState>([]);

  const table = useReactTable({
    data,
    columns,
    state: {
      sorting,
    },
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    initialState: {
      pagination: {
        pageSize,
      },
    },
  });

  if (data.length === 0) {
    return <EmptyState title="Sem registros" cause={emptyMessage} />;
  }

  const pageCount = table.getPageCount();
  const currentPage =
    table.getState().pagination.pageIndex + 1;

  return (
    <div className="space-y-3">
      <div className="rounded-[var(--radius-md)] border border-line bg-panel">
        <Table containerClassName="table-scroll max-h-[70vh] overflow-auto">
          <TableHeader className="sticky top-0 z-10 bg-panel">
            {table.getHeaderGroups().map((headerGroup) => (
              <TableRow key={headerGroup.id}>
                {headerGroup.headers.map((header) => {
                  const sortable =
                    header.column.getCanSort();

                  const sorted =
                    header.column.getIsSorted();

                  const ariaSort = sortable
                    ? sorted === "asc"
                      ? "ascending"
                      : sorted === "desc"
                        ? "descending"
                        : "none"
                    : undefined;

                  return (
                    <TableHead
                      key={header.id}
                      className={alinhamento(header.column.columnDef.meta)}
                      aria-sort={ariaSort}
                    >
                      {header.isPlaceholder ? null : sortable ? (
                        <button
                          type="button"
                          onClick={header.column.getToggleSortingHandler()}
                          className="inline-flex cursor-pointer items-center gap-1 hover:text-primary"
                        >
                          {flexRender(
                            header.column.columnDef.header,
                            header.getContext(),
                          )}

                          {sorted === "asc" && (
                            <span aria-hidden="true">↑</span>
                          )}

                          {sorted === "desc" && (
                            <span aria-hidden="true">↓</span>
                          )}
                        </button>
                      ) : (
                        <span className="inline-flex items-center gap-1">
                          {flexRender(
                            header.column.columnDef.header,
                            header.getContext(),
                          )}
                        </span>
                      )}
                    </TableHead>
                  );
                })}
              </TableRow>
            ))}
          </TableHeader>

          <TableBody>
            {table.getRowModel().rows.map((row) => (
              <TableRow key={row.id}>
                {row.getVisibleCells().map((cell) => (
                  <TableCell
                    key={cell.id}
                    className={alinhamento(cell.column.columnDef.meta)}
                  >
                    {flexRender(
                      cell.column.columnDef.cell,
                      cell.getContext(),
                    )}
                  </TableCell>
                ))}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      {pageCount > 1 && (
        <div className="flex flex-col gap-3 text-sm text-muted sm:flex-row sm:items-center sm:justify-between">
          <span>
            Página {currentPage} de {pageCount}
          </span>

          <div className="flex gap-2">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => table.previousPage()}
              disabled={!table.getCanPreviousPage()}
              className="flex-1 sm:flex-none"
            >
              Anterior
            </Button>

            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => table.nextPage()}
              disabled={!table.getCanNextPage()}
              className="flex-1 sm:flex-none"
            >
              Próxima
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
