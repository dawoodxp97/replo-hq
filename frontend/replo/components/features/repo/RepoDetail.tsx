'use client';

import React, { useState, useMemo, memo } from 'react';
import { Card, Tree, Spin, Empty, Button, Tag } from 'antd';
import type { DataNode } from 'antd/es/tree';
import { useQuery } from '@tanstack/react-query';
import { Editor } from '@monaco-editor/react';
import {
  FolderOpen,
  File,
  ArrowLeft,
  Github,
  FileCode,
  Loader2,
  Clock,
  XCircle,
} from 'lucide-react';
import {
  getRepositoryFileTree,
  getRepositoryFileContent,
  type FileTreeNode,
  type Repository,
} from '@/services/repoService';
import {
  borderGradientDefault,
  backgroundGradientDefault,
  boxShadows,
} from '@/constants/gradientColors';

interface RepoDetailProps {
  repo: Repository;
  onBack: () => void;
}

const getLanguageFromPath = (path: string): string => {
  const ext = path.split('.').pop()?.toLowerCase() || '';
  const languageMap: Record<string, string> = {
    js: 'javascript',
    jsx: 'javascript',
    ts: 'typescript',
    tsx: 'typescript',
    py: 'python',
    java: 'java',
    cpp: 'cpp',
    c: 'c',
    go: 'go',
    rs: 'rust',
    rb: 'ruby',
    php: 'php',
    json: 'json',
    md: 'markdown',
    yml: 'yaml',
    yaml: 'yaml',
    html: 'html',
    css: 'css',
    scss: 'scss',
    less: 'less',
    sh: 'shell',
    bash: 'bash',
    zsh: 'zsh',
    sql: 'sql',
    xml: 'xml',
    txt: 'text',
    ini: 'ini',
    conf: 'ini',
    config: 'ini',
    env: 'ini',
    gitignore: 'plaintext',
    dockerfile: 'dockerfile',
  };
  return languageMap[ext] || 'plaintext';
};

const convertToTreeData = (
  nodes: FileTreeNode[],
  repoId: string
): DataNode[] => {
  return nodes.map((node) => ({
    title: (
      <div className="flex items-center gap-2">
        {node.type === 'directory' ? (
          <FolderOpen className="w-4 h-4 text-blue-500" />
        ) : (
          <File className="w-4 h-4 text-gray-500" />
        )}
        <span className="text-sm">{node.name}</span>
      </div>
    ),
    key: node.path,
    isLeaf: node.type === 'file',
    children: node.children ? convertToTreeData(node.children, repoId) : undefined,
  }));
};

const RepoDetail = ({ repo, onBack }: RepoDetailProps) => {
  const [selectedFile, setSelectedFile] = useState<string | null>(null);
  const [expandedKeys, setExpandedKeys] = useState<React.Key[]>([]);

  const { data: treeData, isLoading: treeLoading } = useQuery({
    queryKey: ['repo-tree', repo.repo_id],
    queryFn: () => getRepositoryFileTree(repo.repo_id),
    enabled: !!repo.repo_id && repo.status === 'COMPLETED',
  });

  const { data: fileContent, isLoading: fileLoading } = useQuery({
    queryKey: ['repo-file', repo.repo_id, selectedFile],
    queryFn: () =>
      getRepositoryFileContent(repo.repo_id, selectedFile!),
    enabled: !!selectedFile && !!repo.repo_id,
  });

  const treeNodes = useMemo(() => {
    if (!treeData?.tree) return [];
    return convertToTreeData(treeData.tree, repo.repo_id);
  }, [treeData, repo.repo_id]);

  const handleSelect = (selectedKeys: React.Key[]) => {
    if (selectedKeys.length > 0) {
      const key = selectedKeys[0] as string;
      // Check if it's a file (not a directory)
      const isFile = treeData?.tree.some(
        (node) => findNodeByPath(node, key)?.type === 'file'
      );
      if (isFile) {
        setSelectedFile(key);
      }
    }
  };

  const findNodeByPath = (
    node: FileTreeNode,
    path: string
  ): FileTreeNode | null => {
    if (node.path === path) return node;
    if (node.children) {
      for (const child of node.children) {
        const found = findNodeByPath(child, path);
        if (found) return found;
      }
    }
    return null;
  };

  const handleExpand = (keys: React.Key[]) => {
    setExpandedKeys(keys);
  };

  if (repo.status !== 'COMPLETED') {
    return (
      <div className="flex flex-col items-center justify-center h-full py-12">
        <Card
          className="max-w-md"
          style={{
            borderRadius: '12px',
            border: 'none',
            background: backgroundGradientDefault,
            boxShadow: boxShadows.default,
          }}
        >
          <div className="text-center space-y-4">
            {repo.status === 'ANALYZING' ? (
              <>
                <Loader2 className="w-12 h-12 text-purple-500 animate-spin mx-auto" />
                <h3 className="text-lg font-semibold text-gray-900">
                  Repository Analyzing
                </h3>
                <p className="text-gray-600">
                  The repository is being analyzed. Please wait...
                </p>
              </>
            ) : repo.status === 'PENDING' ? (
              <>
                <Clock className="w-12 h-12 text-blue-500 mx-auto" />
                <h3 className="text-lg font-semibold text-gray-900">
                  Repository Pending
                </h3>
                <p className="text-gray-600">
                  The repository is queued for analysis.
                </p>
              </>
            ) : (
              <>
                <XCircle className="w-12 h-12 text-red-500 mx-auto" />
                <h3 className="text-lg font-semibold text-gray-900">
                  Repository Failed
                </h3>
                <p className="text-gray-600">
                  The repository analysis failed. Please try again.
                </p>
              </>
            )}
            <Button onClick={onBack} className="mt-4">
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to Repositories
            </Button>
          </div>
        </Card>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="mb-4">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-3">
            <Button
              icon={<ArrowLeft className="w-4 h-4" />}
              onClick={onBack}
              className="flex items-center"
            >
              Back
            </Button>
            <div className="flex items-center gap-2">
              <Github className="w-5 h-5 text-purple-600" />
              <h1 className="text-2xl font-bold text-gray-900">
                {repo.name || 'Repository'}
              </h1>
            </div>
          </div>
          <Tag color="success">Completed</Tag>
        </div>
        <p className="text-sm text-gray-600 ml-12">
          {repo.github_url}
        </p>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex gap-4 overflow-hidden">
        {/* File Tree Sidebar */}
        <Card
          className="flex-shrink-0 w-80 overflow-auto"
          style={{
            borderRadius: '12px',
            border: 'none',
            background: backgroundGradientDefault,
            boxShadow: boxShadows.default,
          }}
          bodyStyle={{ padding: '16px' }}
        >
          <div className="flex items-center gap-2 mb-4">
            <FileCode className="w-5 h-5 text-purple-600" />
            <h2 className="font-semibold text-gray-900">File Tree</h2>
          </div>
          {treeLoading ? (
            <div className="flex justify-center py-8">
              <Spin />
            </div>
          ) : treeNodes.length === 0 ? (
            <Empty
              description="No files found"
              image={Empty.PRESENTED_IMAGE_SIMPLE}
            />
          ) : (
            <Tree
              showLine
              showIcon={false}
              treeData={treeNodes}
              onSelect={handleSelect}
              onExpand={handleExpand}
              expandedKeys={expandedKeys}
              selectedKeys={selectedFile ? [selectedFile] : []}
              className="repo-file-tree"
            />
          )}
        </Card>

        {/* Code Viewer */}
        <Card
          className="flex-1 overflow-auto"
          style={{
            borderRadius: '12px',
            border: 'none',
            background: backgroundGradientDefault,
            boxShadow: boxShadows.default,
          }}
          bodyStyle={{ padding: '0', height: '100%', display: 'flex', flexDirection: 'column' }}
        >
          {!selectedFile ? (
            <div className="flex-1 flex items-center justify-center">
              <Empty
                description="Select a file from the tree to view its contents"
                image={Empty.PRESENTED_IMAGE_SIMPLE}
              />
            </div>
          ) : fileLoading ? (
            <div className="flex-1 flex items-center justify-center">
              <Spin size="large" />
            </div>
          ) : fileContent ? (
            <div className="flex-1 flex flex-col h-full">
              <div className="px-4 py-3 border-b border-gray-200/50 bg-gray-50/50">
                <div className="flex items-center gap-2">
                  <File className="w-4 h-4 text-gray-500" />
                  <span className="text-sm font-medium text-gray-700">
                    {fileContent.path}
                  </span>
                  <span className="text-xs text-gray-500">
                    ({(fileContent.size / 1024).toFixed(2)} KB)
                  </span>
                </div>
              </div>
              <div className="flex-1 overflow-auto">
                <Editor
                  height="100%"
                  language={getLanguageFromPath(fileContent.path)}
                  value={fileContent.content}
                  theme="vs-light"
                  options={{
                    readOnly: true,
                    minimap: { enabled: true },
                    scrollBeyondLastLine: false,
                    fontSize: 14,
                    wordWrap: 'on',
                    lineNumbers: 'on',
                    automaticLayout: true,
                  }}
                />
              </div>
            </div>
          ) : (
            <div className="flex-1 flex items-center justify-center">
              <Empty
                description="Failed to load file content"
                image={Empty.PRESENTED_IMAGE_SIMPLE}
              />
            </div>
          )}
        </Card>
      </div>

      <style jsx global>{`
        .repo-file-tree .ant-tree-node-content-wrapper {
          padding: 4px 8px;
          border-radius: 6px;
          transition: all 0.2s;
        }
        .repo-file-tree .ant-tree-node-content-wrapper:hover {
          background: rgba(99, 102, 241, 0.1);
        }
        .repo-file-tree .ant-tree-node-selected .ant-tree-node-content-wrapper {
          background: rgba(99, 102, 241, 0.15);
        }
      `}</style>
    </div>
  );
};

export default memo(RepoDetail);

