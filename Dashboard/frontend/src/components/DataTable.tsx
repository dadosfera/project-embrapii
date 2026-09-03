import { useMemo, useState } from "react";

import {
  type ColumnDef,
  flexRender,
  getCoreRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  type SortingState,
  useReactTable,
} from "@tanstack/react-table";

type DataTableProps<TData> = {
  data: TData[];
  columns: ColumnDef<TData, unknown>[];
  emptyMessage?: string;
  pageSize?: number;
};

export function DataTable<TData>({
  data,
  columns,
  emptyMessage = "Nenhum registro encontrado.",
  pageSize = 10,
}: DataTableProps<TData>) {
  const [sorting, setSorting] = useState<SortingState>([]);

  const stableData = useMemo(
    () => data,
    [data],
  );

  const table = useReactTable({
    data: stableData,
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
    return (
      <div className="rounded-xl border border-dashed border-teal-100 bg-teal-50/50 px-4 py-8 text-center text-sm text-slate-500">
        {emptyMessage}
      </div>
    );
  }

  const pageCount = table.getPageCount();
  const currentPage =
    table.getState().pagination.pageIndex + 1;

  return (
    <div className="space-y-3">
      <div className="table-scroll rounded-xl border border-teal-100 bg-white">
        <table className="min-w-full border-collapse text-left text-sm">
          <thead className="bg-teal-50/60">
            {table.getHeaderGroups().map((headerGroup) => (
              <tr key={headerGroup.id}>
                {headerGroup.headers.map((header) => {
                  const sortable =
                    header.column.getCanSort();

                  const sorted =
                    header.column.getIsSorted();

                  return (
                    <th
                      key={header.id}
                      className="whitespace-nowrap border-b border-slate-200 px-4 py-3 font-semibold text-slate-700"
                    >
                      {header.isPlaceholder ? null : (
                        <button
                          type="button"
                          disabled={!sortable}
                          onClick={
                            sortable
                              ? header.column.getToggleSortingHandler()
                              : undefined
                          }
                          className={[
                            "inline-flex items-center gap-1",
                            sortable
                              ? "cursor-pointer hover:text-teal-800"
                              : "cursor-default",
                          ].join(" ")}
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
                      )}
                    </th>
                  );
                })}
              </tr>
            ))}
          </thead>

          <tbody>
            {table.getRowModel().rows.map((row) => (
              <tr
                key={row.id}
                className="border-b border-slate-100 last:border-0 hover:bg-teal-50/60/80"
              >
                {row.getVisibleCells().map((cell) => (
                  <td
                    key={cell.id}
                    className="whitespace-nowrap px-4 py-3 text-slate-700"
                  >
                    {flexRender(
                      cell.column.columnDef.cell,
                      cell.getContext(),
                    )}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {pageCount > 1 && (
        <div className="flex flex-col gap-3 text-sm text-slate-600 sm:flex-row sm:items-center sm:justify-between">
          <span>
            Página {currentPage} de {pageCount}
          </span>

          <div className="flex gap-2">
            <button
              type="button"
              onClick={() => table.previousPage()}
              disabled={!table.getCanPreviousPage()}
              className="min-h-10 flex-1 rounded-lg border border-teal-200 bg-white px-3 font-medium transition hover:bg-teal-50/60 disabled:cursor-not-allowed disabled:opacity-50 sm:flex-none"
            >
              Anterior
            </button>

            <button
              type="button"
              onClick={() => table.nextPage()}
              disabled={!table.getCanNextPage()}
              className="min-h-10 flex-1 rounded-lg border border-teal-200 bg-white px-3 font-medium transition hover:bg-teal-50/60 disabled:cursor-not-allowed disabled:opacity-50 sm:flex-none"
            >
              Próxima
            </button>
          </div>
        </div>
      )}
    </div>
  );
}