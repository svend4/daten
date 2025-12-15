/**
 * Documents page - Document management
 */

import React, { useState } from 'react';
import {
  Box,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  Button,
  IconButton,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
} from '@mui/material';
import {
  CloudUpload,
  Delete,
  Visibility,
  Download,
} from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { apiClient } from '../api/client';
import { useDropzone } from 'react-dropzone';

interface Document {
  id: string;
  title: string;
  document_type: string;
  category: string;
  created_at: string;
  domain_name: string;
}

export default function Documents() {
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [uploadOpen, setUploadOpen] = useState(false);
  const queryClient = useQueryClient();

  // Fetch documents
  const { data, isLoading } = useQuery<{ items: Document[]; total: number }>(
    ['documents', page, rowsPerPage],
    () => apiClient.get('/api/documents/', {
      params: {
        limit: rowsPerPage,
        offset: page * rowsPerPage
      }
    }).then(r => r.data)
  );

  // Upload mutation
  const uploadMutation = useMutation(
    (formData: FormData) => apiClient.post('/api/documents/upload', formData),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('documents');
        setUploadOpen(false);
      }
    }
  );

  // File dropzone
  const { getRootProps, getInputProps, acceptedFiles } = useDropzone({
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'text/plain': ['.txt'],
    },
    maxFiles: 1,
  });

  const handleUpload = () => {
    if (acceptedFiles.length > 0) {
      const formData = new FormData();
      formData.append('file', acceptedFiles[0]);
      formData.append('domain_name', 'SGB-IX');
      
      uploadMutation.mutate(formData);
    }
  };

  const handleDelete = async (id: string) => {
    if (window.confirm('Delete this document?')) {
      await apiClient.delete(`/api/documents/${id}`);
      queryClient.invalidateQueries('documents');
    }
  };

  if (isLoading || !data) {
    return <div>Loading...</div>;
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
        <h2>Documents</h2>
        <Button
          variant="contained"
          startIcon={<CloudUpload />}
          onClick={() => setUploadOpen(true)}
        >
          Upload Document
        </Button>
      </Box>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Title</TableCell>
              <TableCell>Type</TableCell>
              <TableCell>Category</TableCell>
              <TableCell>Domain</TableCell>
              <TableCell>Created</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {data.items.map((doc) => (
              <TableRow key={doc.id}>
                <TableCell>{doc.title}</TableCell>
                <TableCell>
                  <Chip label={doc.document_type} size="small" />
                </TableCell>
                <TableCell>{doc.category}</TableCell>
                <TableCell>{doc.domain_name}</TableCell>
                <TableCell>
                  {new Date(doc.created_at).toLocaleDateString()}
                </TableCell>
                <TableCell align="right">
                  <IconButton size="small">
                    <Visibility />
                  </IconButton>
                  <IconButton size="small">
                    <Download />
                  </IconButton>
                  <IconButton
                    size="small"
                    color="error"
                    onClick={() => handleDelete(doc.id)}
                  >
                    <Delete />
                  </IconButton>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
        <TablePagination
          component="div"
          count={data.total}
          page={page}
          onPageChange={(_, newPage) => setPage(newPage)}
          rowsPerPage={rowsPerPage}
          onRowsPerPageChange={(e) => setRowsPerPage(parseInt(e.target.value))}
        />
      </TableContainer>

      {/* Upload Dialog */}
      <Dialog open={uploadOpen} onClose={() => setUploadOpen(false)}>
        <DialogTitle>Upload Document</DialogTitle>
        <DialogContent>
          <Box
            {...getRootProps()}
            sx={{
              border: '2px dashed #ccc',
              borderRadius: 2,
              p: 3,
              textAlign: 'center',
              cursor: 'pointer',
              '&:hover': { borderColor: 'primary.main' }
            }}
          >
            <input {...getInputProps()} />
            <CloudUpload sx={{ fontSize: 48, color: 'text.secondary' }} />
            <p>Drag & drop a file here, or click to select</p>
            {acceptedFiles.length > 0 && (
              <p>Selected: {acceptedFiles[0].name}</p>
            )}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setUploadOpen(false)}>Cancel</Button>
          <Button
            onClick={handleUpload}
            variant="contained"
            disabled={acceptedFiles.length === 0 || uploadMutation.isLoading}
          >
            Upload
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}