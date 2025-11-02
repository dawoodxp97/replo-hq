import { memo } from 'react';
import EmptyState, { EmptyStateProps } from './EmptyState';

export interface EmptyTableRowProps extends Omit<EmptyStateProps, 'variant'> {
  colSpan?: number;
}

const EmptyTableRow = ({ colSpan = 1, ...emptyStateProps }: EmptyTableRowProps) => {
  return (
    <tr>
      <td colSpan={colSpan} className="p-0">
        <EmptyState variant="table" {...emptyStateProps} />
      </td>
    </tr>
  );
};

export default memo(EmptyTableRow);

