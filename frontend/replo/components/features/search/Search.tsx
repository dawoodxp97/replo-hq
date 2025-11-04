import React, { useMemo, useRef, useState, memo, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { Select, Spin, Avatar, Tag } from 'antd';
import type { SelectProps } from 'antd';
import { debounce } from 'lodash';
import {
  searchEntities,
  type EntityValue as SearchEntityValue,
} from '@/services/searchService';
import { SearchOutlined } from '@ant-design/icons';
import { TextSearch } from 'lucide-react';
import {
  borderGradientDefault,
  borderGradientHover,
  borderGradientFocus,
  backgroundGradientDefault,
  backgroundGradientHover,
  backgroundGradientFocus,
  boxShadows,
  dropdownGradientHover,
  dropdownGradientSelected,
} from '@/constants/gradientColors';

interface EntityValue {
  id: string;
  label: string;
  type: 'repository' | 'tutorial' | 'module' | 'quiz';
  avatar?: string;
  tutorial_id?: string;
  module_index?: number;
}

export interface DebounceSelectProps<ValueType = any>
  extends Omit<SelectProps<ValueType | ValueType[]>, 'options' | 'children'> {
  fetchOptions: (search: string) => Promise<ValueType[]>;
  debounceTimeout?: number;
}

// Extended type that includes both Ant Design's required fields and our EntityValue
type SelectOptionValue = SearchEntityValue & {
  value: string;
  key?: string;
};

// Type icons mapping
const getTypeIcon = (type: EntityValue['type']) => {
  const icons = {
    repository: '📦',
    tutorial: '📚',
    module: '📄',
    quiz: '❓',
  };
  return icons[type] || '📌';
};

// Type color mapping
const getTypeColor = (type: EntityValue['type']) => {
  const colors = {
    repository: 'blue',
    tutorial: 'purple',
    module: 'green',
    quiz: 'orange',
  };
  return colors[type] || 'default';
};

function DebounceSelect<
  ValueType extends {
    key?: string;
    label: React.ReactNode;
    value: string | number;
    avatar?: string;
    type?: SearchEntityValue['type'];
  } = any
>({
  fetchOptions,
  debounceTimeout = 300,
  ...props
}: DebounceSelectProps<ValueType>) {
  const [fetching, setFetching] = useState(false);
  const [options, setOptions] = useState<ValueType[]>([]);
  const [open, setOpen] = useState(false);
  const fetchRef = useRef(0);

  const debounceFetcher = useMemo(() => {
    const loadOptions = (value: string) => {
      if (!value || value.trim().length === 0) {
        setOptions([]);
        setFetching(false);
        return;
      }

      fetchRef.current += 1;
      const fetchId = fetchRef.current;
      setFetching(true);

      fetchOptions(value)
        .then(newOptions => {
          if (fetchId !== fetchRef.current) {
            // for fetch callback order
            return;
          }

          console.log('Search results received:', newOptions);
          // Options are already in the correct format from handleSearch
          // They should have label, value, and all entity fields
          setOptions(newOptions as ValueType[]);
          setFetching(false);
          // Open dropdown if we have results
          if (newOptions.length > 0) {
            setOpen(true);
          }
        })
        .catch(error => {
          if (fetchId !== fetchRef.current) {
            return;
          }
          console.error('Search error:', error);
          setOptions([]);
          setFetching(false);
        });
    };

    return debounce(loadOptions, debounceTimeout);
  }, [fetchOptions, debounceTimeout]);

  return (
    <Select
      labelInValue
      filterOption={false}
      open={open}
      onDropdownVisibleChange={setOpen}
      onSearch={value => {
        if (value.trim().length > 0) {
          setOpen(true);
        }
        debounceFetcher(value);
      }}
      onFocus={() => {
        // Open dropdown if there are options
        if (options.length > 0) {
          setOpen(true);
        }
      }}
      onBlur={() => {
        // Keep dropdown open briefly to allow selection
        setTimeout(() => setOpen(false), 200);
      }}
      loading={fetching}
      notFoundContent={
        fetching ? (
          <div className="flex items-center justify-center py-6">
            <Spin size="default" />
            <span className="ml-3 text-gray-600 font-medium">Searching...</span>
          </div>
        ) : options.length === 0 && !fetching ? (
          <div className="py-6 text-center text-gray-400 text-sm">
            No results found. Try a different search term.
          </div>
        ) : null
      }
      {...props}
      options={options}
      optionRender={option => {
        // Find the full entity data from options array
        const fullOption = options.find(
          opt => String(opt.value) === String(option.value)
        );
        const entity = (fullOption || option) as unknown as SelectOptionValue;
        const type = entity?.type || 'repository';
        return (
          <div className="flex items-center gap-3 py-1">
            <div className="flex-shrink-0 text-lg">{getTypeIcon(type)}</div>
            {entity?.avatar ? (
              <Avatar
                src={entity.avatar}
                size="small"
                className="flex-shrink-0"
              />
            ) : (
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-400 to-purple-500 flex items-center justify-center text-white text-xs font-semibold flex-shrink-0">
                {entity?.label?.toString().charAt(0).toUpperCase() || '?'}
              </div>
            )}
            <div className="flex-1 min-w-0">
              <div className="font-medium text-gray-900 truncate">
                {option.label}
              </div>
              {type && (
                <Tag color={getTypeColor(type)} className="mt-1 text-xs">
                  {type}
                </Tag>
              )}
            </div>
          </div>
        );
      }}
      className="w-full"
      showSearch
      allowClear
      size="large"
      suffixIcon={<TextSearch className="text-purple-500 w-4 h-4" />}
    />
  );
}

const Search = () => {
  const router = useRouter();
  const [selectedValues, setSelectedValues] = useState<EntityValue[]>([]);
  const [isSearching, setIsSearching] = useState(false);

  const handleSearch = useCallback(
    async (query: string): Promise<SelectOptionValue[]> => {
      if (!query || query.trim().length === 0) {
        return [];
      }

      try {
        setIsSearching(true);
        const results = await searchEntities(query.trim());
        return results.map(entity => ({
          ...entity,
          value: entity.id,
          key: entity.id,
        }));
      } catch (error) {
        console.error('Search failed:', error);
        return [];
      } finally {
        setIsSearching(false);
      }
    },
    []
  );

  const navigateToEntity = useCallback(
    (entity: SelectOptionValue) => {
      switch (entity.type) {
        case 'repository':
          router.push(`/repo/${entity.id}`);
          break;
        case 'tutorial':
          router.push(`/tutorial/${entity.id}`);
          break;
        case 'module':
          // Navigate to the parent tutorial and jump to the specific module
          if (entity.tutorial_id) {
            const moduleIndex =
              entity.module_index !== undefined ? entity.module_index : 0;
            router.push(
              `/tutorial/${entity.tutorial_id}?module=${moduleIndex}`
            );
          } else {
            console.error('Module missing tutorial_id:', entity);
          }
          break;
        case 'quiz':
          // Navigate to the parent tutorial and jump to the module containing the quiz
          if (entity.tutorial_id) {
            const moduleIndex =
              entity.module_index !== undefined ? entity.module_index : 0;
            router.push(
              `/tutorial/${entity.tutorial_id}?module=${moduleIndex}`
            );
          } else {
            console.error('Quiz missing tutorial_id:', entity);
          }
          break;
        default:
          console.log('Unknown entity type:', entity);
      }

      // Clear selection after navigation
      setTimeout(() => {
        setSelectedValues([]);
      }, 300);
    },
    [router]
  );

  const handleChange = useCallback(
    (newValue: SelectOptionValue | SelectOptionValue[] | null) => {
      if (!newValue) {
        setSelectedValues([]);
        return;
      }

      const values = Array.isArray(newValue) ? newValue : [newValue];
      setSelectedValues(
        values.map(v => ({
          id: v.id,
          label: v.label,
          type: v.type,
          avatar: v.avatar,
          tutorial_id: v.tutorial_id,
          module_index: v.module_index,
        }))
      );

      // Navigate to the first selected item
      if (values.length > 0) {
        const firstEntity = values[0];
        navigateToEntity(firstEntity);
      }
    },
    [navigateToEntity]
  );

  const handleClear = useCallback(() => {
    setSelectedValues([]);
  }, []);

  return (
    <div className="searchbar-container w-full max-w-2xl relative">
      <div className="gradient-border-wrapper">
        <DebounceSelect
          mode="multiple"
          value={
            selectedValues.length > 0
              ? selectedValues.map(v => ({
                  label: v.label,
                  value: v.id,
                  key: v.id,
                  id: v.id,
                  type: v.type,
                  avatar: v.avatar,
                  tutorial_id: v.tutorial_id,
                  module_index: v.module_index,
                }))
              : undefined
          }
          placeholder="Search repositories, tutorials, modules, or quizzes..."
          fetchOptions={handleSearch}
          onChange={handleChange}
          onClear={handleClear}
          loading={isSearching}
          maxTagCount={2}
          maxTagPlaceholder={omittedValues => `+${omittedValues.length} more`}
          tagRender={props => {
            const { label, value, onClose } = props;
            const entity = selectedValues.find(e => e.id === value);
            return (
              <Tag
                closable
                onClose={onClose}
                color={entity ? getTypeColor(entity.type) : 'default'}
                className="flex items-center gap-1 px-2 py-1 rounded-md text-xs font-medium"
              >
                <span>{entity ? getTypeIcon(entity.type) : ''}</span>
                <span className="max-w-[120px] truncate">{label}</span>
              </Tag>
            );
          }}
          style={{
            width: '450px',
            height: '40px',
          }}
        />
      </div>
      {/* 
        Custom styles for Ant Design Select component
        Why needed: Ant Design uses CSS-in-JS with class names that we can't fully override with Tailwind alone.
        These styles customize:
        1. Dropdown item padding & hover states (better UX)
        2. Select input border radius & focus states (matches Tailwind design)
        3. Selected option background (visual feedback)
        
        Alternative: Move to globals.css if preferred, but keeping here for component isolation.
      */}
      <style jsx global>{`
        /* Dropdown menu item styling */
        .search-dropdown .ant-select-item {
          padding: 10px 16px !important;
          transition: background-color 0.2s ease;
        }
        .search-dropdown .ant-select-item:hover {
          background: ${dropdownGradientHover} !important;
        }
        .search-dropdown .ant-select-item-option-selected {
          background: ${dropdownGradientSelected} !important;
        }

        /* Gradient border wrapper - AI-inspired design */
        .searchbar-container .gradient-border-wrapper {
          position: relative;
          border-radius: 0.75rem;
          padding: 1px;
          background: ${borderGradientDefault};
          transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }

        .searchbar-container .gradient-border-wrapper:hover {
          background: ${borderGradientHover};
          box-shadow: ${boxShadows.hover};
        }

        /* AI-inspired input field styling with light gradient background */
        .searchbar-container .ant-select-selector {
          border-radius: 0.625rem !important;
          border: none !important;
          background: ${backgroundGradientDefault} !important;
          transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
          box-shadow: ${boxShadows.default} !important;
        }

        .searchbar-container
          .gradient-border-wrapper:hover
          .ant-select-selector {
          background: ${backgroundGradientHover} !important;
          box-shadow: ${boxShadows.hover} !important;
        }

        /* Focus state - bold gradient border with enhanced effects */
        .searchbar-container:has(.ant-select-focused) .gradient-border-wrapper {
          background: ${borderGradientFocus} !important;
          padding: 1.5px !important;
          box-shadow: ${boxShadows.focus} !important;
          transform: translateY(-1px) !important;
        }

        .searchbar-container .ant-select-focused .ant-select-selector {
          background: ${backgroundGradientFocus} !important;
          box-shadow: ${boxShadows.focusInset} !important;
        }
      `}</style>
    </div>
  );
};

export default memo(Search);
